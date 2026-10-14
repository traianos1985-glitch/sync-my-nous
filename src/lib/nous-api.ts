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
  // Honour an explicit absolute override (own staging backend), but never a
  // relative one: it would send dashboard calls back to the HTML-only origin.
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

function readStorage(storage: Storage, key: string): string | undefined {
  try {
    return storage.getItem(key) || undefined;
  } catch {
    return undefined;
  }
}

function writeStorage(storage: Storage, key: string, value: string): boolean {
  try {
    storage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

function readTokenCookie(): string | undefined {
  if (typeof document === "undefined") return undefined;
  const cookie = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${tokenStorageKey}=`));
  if (!cookie) return undefined;
  try {
    return decodeURIComponent(cookie.slice(tokenStorageKey.length + 1)) || undefined;
  } catch {
    return undefined;
  }
}

function writeTokenCookie(token: string): boolean {
  if (typeof document === "undefined") return false;
  try {
    document.cookie = `${tokenStorageKey}=${encodeURIComponent(token)}; Max-Age=31536000; Path=/; SameSite=Lax${
      window.location.protocol === "https:" ? "; Secure" : ""
    }`;
    return readTokenCookie() === token;
  } catch {
    return false;
  }
}

function clearTokenCookie(): void {
  if (typeof document === "undefined") return;
  try {
    document.cookie = `${tokenStorageKey}=; Max-Age=0; Path=/; SameSite=Lax${
      window.location.protocol === "https:" ? "; Secure" : ""
    }`;
  } catch {
    // Storage cleanup is best effort in privacy-restricted preview contexts.
  }
}

function getStoredToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  // Keep the token across reloads, preview iframe navigation, and chat routes.
  // Storage can be blocked in privacy-restricted iframes, so use a first-party
  // cookie as a durable fallback. The value only leaves the browser as a bearer
  // Authorization header to the NOUS API.
  return (
    readStorage(window.localStorage, tokenStorageKey) ||
    readStorage(window.sessionStorage, tokenStorageKey) ||
    readTokenCookie()
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
  if (typeof window !== "undefined") {
    // Write to every browser persistence layer that may be available. This
    // makes Save reliable when preview privacy settings block one mechanism.
    writeStorage(window.localStorage, tokenStorageKey, normalizedToken);
    writeStorage(window.sessionStorage, tokenStorageKey, normalizedToken);
    writeTokenCookie(normalizedToken);
    if (!getStoredToken()) {
      throw new Error("Δεν ήταν δυνατή η αποθήκευση του NOUS token σε αυτό το preview.");
    }
  }
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
    try {
      window.localStorage.removeItem(tokenStorageKey);
    } catch {
      // Ignore blocked storage during cleanup.
    }
    try {
      window.sessionStorage.removeItem(tokenStorageKey);
    } catch {
      // Ignore blocked storage during cleanup.
    }
    clearTokenCookie();
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
