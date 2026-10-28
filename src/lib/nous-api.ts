import {
  backendWakeTracker,
  REQUEST_TIMEOUT_MS,
  SLOW_REQUEST_MS,
  RECOVERY_DELAY_MS,
  GATEWAY_STATUSES,
} from "./backend-wake-state";

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

const apiBase = RENDER_API_BASE;
export function getNousApiBase(): string {
  return apiBase;
}
const tokenStorageKey = "nous-dashboard-token";

export function subscribeBackendWaking(listener: (waking: boolean) => void): () => void {
  const notify = () => listener(backendWakeTracker.getSnapshot().phase !== "idle");
  notify();
  return backendWakeTracker.subscribe(notify);
}

function waitForRenderRecovery(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    signal.throwIfAborted();
    const abort = () => {
      clearTimeout(timer);
      reject(signal.reason);
    };
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve();
    }, RECOVERY_DELAY_MS);
    signal.addEventListener("abort", abort, { once: true });
  });
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

// One lifecycle for JSON and streaming headers. Mutations are never auto-replayed.
async function executeRequest<T>(
  path: string,
  options: NousApiOptions,
  accept: string,
  read: (response: Response) => Promise<T>,
): Promise<T> {
  options.signal?.throwIfAborted();
  if (!path.startsWith("/") || path.startsWith("//") || /[\\\r\n]/.test(path)) {
    throw new Error("Invalid NOUS API path");
  }
  const headers = new Headers(options.headers);
  headers.set("Accept", accept);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  setAuthorizationHeader(headers, options.token ?? getNousToken());
  const controller = new AbortController();
  const callerSignal = options.signal;
  const abort = () => controller.abort(callerSignal?.reason);
  callerSignal?.addEventListener("abort", abort, { once: true });
  const id = backendWakeTracker.begin();
  const slowTimer = setTimeout(() => backendWakeTracker.markSlow(id), SLOW_REQUEST_MS);
  const timeout = setTimeout(
    () => controller.abort(new DOMException("Timeout", "TimeoutError")),
    options.timeoutMs ?? REQUEST_TIMEOUT_MS,
  );
  const { token: _token, timeoutMs: _timeoutMs, ...requestInit } = options;
  const request: RequestInit = {
    ...requestInit,
    body: adaptBody(path, options.body),
    headers,
    credentials: "omit",
    signal: controller.signal,
  };
  try {
    for (let attempt = 0; ; attempt += 1) {
      controller.signal.throwIfAborted();
      const response = await fetch(requestUrl(path), request);
      if (GATEWAY_STATUSES.has(response.status)) {
        backendWakeTracker.gatewayFailure();
        if (attempt === 0 && (request.method ?? "GET").toUpperCase() === "GET") {
          await response.body?.cancel();
          await waitForRenderRecovery(controller.signal);
          continue;
        }
      } else {
        // Even 401/404 proves Render is awake; do not leave a stale wake banner.
        backendWakeTracker.reachable();
      }
      if (!response.ok) throw await createApiError(response);
      const value = await read(response);
      controller.signal.throwIfAborted();
      return value;
    }
  } catch (error) {
    if (callerSignal?.aborted) throw new DOMException("Request aborted", "AbortError");
    if (controller.signal.aborted)
      throw new NousApiError(
        408,
        "Η αναμονή έληξε. Το Render μπορεί ακόμη να εκκινείται. Δοκίμασε ξανά.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
    clearTimeout(slowTimer);
    callerSignal?.removeEventListener("abort", abort);
    backendWakeTracker.finish(id);
  }
}

// Stream callers own body-reading cancellation after the response headers arrive.
export function nousStream(path: string, options: NousApiOptions = {}): Promise<Response> {
  return executeRequest(path, options, "text/event-stream", async (response) => response);
}
export function nousFetch<T>(path: string, options: NousApiOptions = {}): Promise<T> {
  return executeRequest(
    path,
    options,
    "application/json",
    async (response) => response.json() as Promise<T>,
  );
}
