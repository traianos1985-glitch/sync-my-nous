export type NousApiOptions = RequestInit & { token?: string; timeoutMs?: number };

export class NousApiError extends Error {
  readonly status: number;
  readonly details?: string;

  constructor(status: number, message: string, details?: string) {
    super(message);
    this.name = "NousApiError";
    this.status = status;
    this.details = details;
  }
}

// Every dashboard request goes straight to the Render service. A relative base
// such as "/api/nous" only works behind the Vite dev proxy — the Lovable preview
// origin answers HTML requests there and rejects API calls with
// "Only HTML requests are supported here".
const RENDER_API_BASE = "https://nous-ai-os-api.onrender.com";

function resolveApiBase(): string {
  const configured = import.meta.env["VITE_NOUS_API_URL"]?.trim();
  const isLocalPreview =
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

  // Local Vite previews use the existing proxy so Render does not reject the
  // ephemeral localhost origin during CORS preflight. Published previews go
  // directly to Render and use its allow-listed preview origins.
  if (isLocalPreview) return "/api/nous";

  const base = configured && /^https?:\/\//i.test(configured) ? configured : RENDER_API_BASE;
  return base.replace(/\/+$/, "");
}

const apiBase = resolveApiBase();
const tokenStorageKey = "nous-dashboard-token";
const requestTimeoutMs = 75_000;

// ---- Cold-start (Render wake-up) signal ----
const slowRequestMs = 4_000;
let pendingSlow = 0;
let gatewayFailures = 0;
const wakeListeners = new Set<(waking: boolean) => void>();
let lastWaking = false;
function emitWake() {
  const waking = pendingSlow > 0 || gatewayFailures >= 2;
  if (waking === lastWaking) return;
  lastWaking = waking;
  wakeListeners.forEach((listener) => listener(waking));
}
export function subscribeBackendWaking(listener: (waking: boolean) => void): () => void {
  wakeListeners.add(listener);
  listener(lastWaking);
  return () => wakeListeners.delete(listener);
}
function trackRequest<T>(run: () => Promise<T>): Promise<T> {
  let slow = false;
  const timer = window.setTimeout(() => {
    slow = true;
    pendingSlow += 1;
    emitWake();
  }, slowRequestMs);
  const finish = () => {
    window.clearTimeout(timer);
    if (slow) pendingSlow -= 1;
    emitWake();
  };
  return run().then(
    (value) => {
      gatewayFailures = 0;
      finish();
      return value;
    },
    (error) => {
      const status = (error as { status?: number })?.status;
      const msg = error instanceof Error ? error.message : "";
      if ((status && [502, 503, 504].includes(status)) || /\((502|503|504)\)/.test(msg)) {
        gatewayFailures += 1;
      } else if (!(error instanceof DOMException)) {
        gatewayFailures = Math.max(0, gatewayFailures);
      }
      finish();
      throw error;
    },
  );
}
const retryableStatuses = new Set([502, 503, 504]);

function shouldRetry(request: RequestInit, response: Response, attempt: number): boolean {
  const method = (request.method ?? "GET").toUpperCase();
  return attempt === 0 && method === "GET" && retryableStatuses.has(response.status);
}

async function waitForRenderRecovery(): Promise<void> {
  await new Promise((resolve) => window.setTimeout(resolve, 1_200));
}

async function createApiError(response: Response): Promise<NousApiError> {
  const body = await response.json().catch(() => null);
  const serverMessage =
    body && typeof body === "object"
      ? "error" in body && typeof body.error === "string"
        ? body.error
        : "message" in body && typeof body.message === "string"
          ? body.message
          : undefined
      : undefined;
  const detailMessage =
    body && typeof body === "object" && "details" in body && typeof body.details === "string"
      ? body.details
      : undefined;
  const message =
    response.status === 401 || response.status === 403
      ? "Το NOUS token απορρίφθηκε. Έλεγξε ή αντικατάστησε το token στις ρυθμίσεις."
      : response.status === 429
        ? "Το Gemini ή το Render επέστρεψε quota limit. Περίμενε λίγο πριν ξαναδοκιμάσεις."
        : response.status === 502 || response.status === 503 || response.status === 504
          ? "Το Render κάνει cold start ή προσωρινή επανεκκίνηση. Δοκίμασε ξανά σε λίγο."
          : (serverMessage ?? `NOUS API request failed (${response.status})`);
  return new NousApiError(response.status, message, detailMessage ?? serverMessage);
}

const BACKEND_PATH_MAP: Record<string, string> = {
  "/api/chat": "/chat",
  "/api/health": "/health",
};

function requestUrl(path: string): string {
  // GitHub Pages serves static files only. Dashboard API calls must always
  // reach the Flask service, where the existing NOUS bearer token is validated.
  return `${apiBase}${resolvePath(path)}`;
}

function resolvePath(path: string): string {
  const [pathname, query] = path.split("?");
  const mapped = BACKEND_PATH_MAP[pathname ?? ""] ?? pathname;
  return query ? `${mapped}?${query}` : (mapped ?? path);
}

function adaptBody(path: string, body: RequestInit["body"]): RequestInit["body"] {
  if (resolvePath(path) !== "/chat" || typeof body !== "string") return body;
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>;
    if (typeof parsed["message"] === "string" && !parsed["command"]) {
      parsed["command"] = parsed["message"];
    }
    if (Array.isArray(parsed["history"])) {
      parsed["history"] = parsed["history"].map((item) => {
        if (!item || typeof item !== "object") return item;
        const entry = item as Record<string, unknown>;
        return {
          ...entry,
          text: typeof entry["text"] === "string" ? entry["text"] : entry["content"],
        };
      });
    }
    if (parsed["conversation_id"] && !parsed["conversationId"]) {
      parsed["conversationId"] = parsed["conversation_id"];
    }
    return JSON.stringify(parsed);
  } catch {
    return body;
  }
}

function getStoredToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  // Keep the token across preview iframe reloads and chat navigation. The value
  // never leaves the browser except as an Authorization header to the NOUS API.
  return (
    window.localStorage.getItem(tokenStorageKey) ||
    window.sessionStorage.getItem(tokenStorageKey) ||
    undefined
  );
}

export function hasConfiguredNousApi(): boolean {
  return Boolean(apiBase);
}

export function hasStoredNousToken(): boolean {
  return Boolean(getStoredToken());
}

export function getNousToken(): string | undefined {
  return getStoredToken()?.trim() || undefined;
}

export function setNousToken(token: string): void {
  const normalizedToken = token.trim();
  if (!normalizedToken) {
    clearNousToken();
    return;
  }
  if ([...normalizedToken].some((character) => character.charCodeAt(0) > 255)) {
    throw new Error("Το NOUS token πρέπει να αποτελείται μόνο από λατινικούς χαρακτήρες.");
  }
  if (typeof window !== "undefined") window.localStorage.setItem(tokenStorageKey, normalizedToken);
}

function setAuthorizationHeader(headers: Headers, token: string | undefined): void {
  if (!token) return;
  if ([...token].some((character) => character.charCodeAt(0) > 255)) {
    throw new Error(
      "Το NOUS token περιέχει μη έγκυρους χαρακτήρες. Κάνε επικόλληση του token χωρίς ελληνικά ή κενά.",
    );
  }
  headers.set("Authorization", `Bearer ${token}`);
}

export function clearNousToken(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(tokenStorageKey);
    window.sessionStorage.removeItem(tokenStorageKey);
  }
}

export function nousStream(path: string, options: NousApiOptions = {}): Promise<Response> {
  return trackRequest(() => nousStreamInner(path, options));
}

async function nousStreamInner(path: string, options: NousApiOptions = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "text/event-stream");
  const token = options.token ?? getNousToken();
  setAuthorizationHeader(headers, token);
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? requestTimeoutMs,
  );
  if (options.signal)
    options.signal.addEventListener("abort", () => controller.abort(), { once: true });
  let response: Response;
  const { token: _token, timeoutMs: _timeoutMs, ...requestInit } = options;
  const request = {
    ...requestInit,
    body: adaptBody(path, options.body),
    headers,
    credentials: "include" as const,
    signal: controller.signal,
  };
  try {
    response = await fetch(requestUrl(path), request);
    if (shouldRetry(request, response, 0)) {
      await waitForRenderRecovery();
      response = await fetch(requestUrl(path), request);
    }
  } catch (error) {
    if (options.signal?.aborted) throw new DOMException("Request aborted", "AbortError");
    if (controller.signal.aborted)
      throw new Error("NOUS API timeout — το Render μπορεί να κάνει cold start. Δοκίμασε ξανά.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) throw await createApiError(response);
  return response;
}

export function nousFetch<T>(path: string, options: NousApiOptions = {}): Promise<T> {
  return trackRequest(() => nousFetchInner<T>(path, options));
}

async function nousFetchInner<T>(path: string, options: NousApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  const token = options.token ?? getNousToken();
  setAuthorizationHeader(headers, token);
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? requestTimeoutMs,
  );
  if (options.signal)
    options.signal.addEventListener("abort", () => controller.abort(), { once: true });
  let response: Response;
  const { token: _token, timeoutMs: _timeoutMs, ...requestInit } = options;
  const request = {
    ...requestInit,
    body: adaptBody(path, options.body),
    headers,
    credentials: "include" as const,
    signal: controller.signal,
  };
  try {
    response = await fetch(requestUrl(path), request);
    if (shouldRetry(request, response, 0)) {
      await waitForRenderRecovery();
      response = await fetch(requestUrl(path), request);
    }
  } catch (error) {
    if (options.signal?.aborted) throw new DOMException("Request aborted", "AbortError");
    if (controller.signal.aborted)
      throw new Error("NOUS API timeout — το Render μπορεί να κάνει cold start. Δοκίμασε ξανά.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) throw await createApiError(response);
  return response.json() as Promise<T>;
}
