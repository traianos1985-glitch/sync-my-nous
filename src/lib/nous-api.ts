export type NousApiOptions = RequestInit & { token?: string; timeoutMs?: number };

const defaultApiBase = import.meta.env.DEV ? "/api/nous" : "https://nous-ai-os-api.onrender.com";
const apiBase = (import.meta.env["VITE_NOUS_API_URL"] || defaultApiBase).replace(/\/$/, "");
const apiToken = import.meta.env["VITE_NOUS_API_TOKEN"];
const tokenStorageKey = "nous-dashboard-token";
const requestTimeoutMs = 35_000;

// The dashboard uses /api/* names, but the Flask backend on Render exposes some
// of them under different paths. Map them so the buttons reach real endpoints.
const BACKEND_PATH_MAP: Record<string, string> = {
  "/api/chat": "/chat",
  "/api/health": "/health",
};

function resolvePath(path: string): string {
  const [pathname, query] = path.split("?");
  const mapped = BACKEND_PATH_MAP[pathname ?? ""] ?? pathname;
  return query ? `${mapped}?${query}` : (mapped ?? path);
}

// Flask /chat reads `command` after its early-return handlers, so mirror `message` into it.
function adaptBody(path: string, body: RequestInit["body"]): RequestInit["body"] {
  if (resolvePath(path) !== "/chat" || typeof body !== "string") return body;
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>;
    if (typeof parsed["message"] === "string" && !parsed["command"]) {
      parsed["command"] = parsed["message"];
    }
    return JSON.stringify(parsed);
  } catch {
    return body;
  }
}

function getStoredToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  return window.sessionStorage.getItem(tokenStorageKey) || undefined;
}

export function hasConfiguredNousApi(): boolean {
  return Boolean(apiBase);
}

export function hasStoredNousToken(): boolean {
  return Boolean(getStoredToken());
}

export function getNousToken(): string | undefined {
  const token = getStoredToken() ?? apiToken;
  return token?.trim() || undefined;
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
  if (typeof window !== "undefined")
    window.sessionStorage.setItem(tokenStorageKey, normalizedToken);
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
  if (typeof window !== "undefined") window.sessionStorage.removeItem(tokenStorageKey);
}

export async function nousStream(path: string, options: NousApiOptions = {}): Promise<Response> {
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
  try {
    const { token: _token, timeoutMs: _timeoutMs, ...requestInit } = options;
    response = await fetch(`${apiBase}${resolvePath(path)}`, {
      ...requestInit,
      body: adaptBody(path, options.body),
      headers,
      credentials: "include",
      signal: controller.signal,
    });
  } catch (error) {
    if (options.signal?.aborted) throw new DOMException("Request aborted", "AbortError");
    if (controller.signal.aborted)
      throw new Error("NOUS API timeout — το Render μπορεί να κάνει cold start. Δοκίμασε ξανά.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) throw new Error(`NOUS stream failed (${response.status})`);
  return response;
}

export async function nousFetch<T>(path: string, options: NousApiOptions = {}): Promise<T> {
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
  try {
    const { token: _token, timeoutMs: _timeoutMs, ...requestInit } = options;
    response = await fetch(`${apiBase}${resolvePath(path)}`, {
      ...requestInit,
      body: adaptBody(path, options.body),
      headers,
      credentials: "include",
      signal: controller.signal,
    });
  } catch (error) {
    if (options.signal?.aborted) throw new DOMException("Request aborted", "AbortError");
    if (controller.signal.aborted)
      throw new Error("NOUS API timeout — το Render μπορεί να κάνει cold start. Δοκίμασε ξανά.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error ?? `NOUS API request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}
