export type NousApiOptions = RequestInit & { token?: string };

const defaultApiBase = import.meta.env.DEV ? "/api/nous" : "https://nous-ai-os-api.onrender.com";
const apiBase = (import.meta.env["VITE_NOUS_API_URL"] || defaultApiBase).replace(/\/$/, "");
const apiToken = import.meta.env["VITE_NOUS_API_TOKEN"];
const tokenStorageKey = "nous-dashboard-token";
const requestTimeoutMs = 35_000;

function getStoredToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  return window.localStorage.getItem(tokenStorageKey) || undefined;
}

export function hasConfiguredNousApi(): boolean {
  return Boolean(apiBase);
}

export function getNousToken(): string | undefined {
  return getStoredToken() ?? apiToken;
}

export function setNousToken(token: string): void {
  if (typeof window !== "undefined") window.localStorage.setItem(tokenStorageKey, token.trim());
}

export function clearNousToken(): void {
  if (typeof window !== "undefined") window.localStorage.removeItem(tokenStorageKey);
}

export async function nousStream(path: string, options: NousApiOptions = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "text/event-stream");
  const token = options.token ?? getNousToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  if (options.signal)
    options.signal.addEventListener("abort", () => controller.abort(), { once: true });
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      ...options,
      headers,
      credentials: "include",
      signal: controller.signal,
    });
  } catch (error) {
    if (controller.signal.aborted)
      throw new Error("NOUS API timeout — το Render μπορεί να κάνει cold start. Δοκίμασε ξανά.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) throw new Error(`NOUS stream failed (${response.status})`);
  return response;
}

export async function streamNousAnswer(
  answer: string,
  onToken: (text: string) => void,
  options: NousApiOptions = {},
): Promise<void> {
  const response = await nousStream("/api/chat/stream", {
    ...options,
    method: "POST",
    body: JSON.stringify({ answer }),
  });
  const reader = response.body?.getReader();
  if (!reader) throw new Error("NOUS stream body unavailable");
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    for (const block of buffer.split("\\n\\n").slice(0, -1)) {
      const line = block.split("\\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const data = JSON.parse(line.slice(6)) as { text?: string };
      if (data.text) onToken(data.text);
    }
    buffer = buffer.split("\\n\\n").at(-1) ?? "";
    if (done) break;
  }
}

export async function nousFetch<T>(path: string, options: NousApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  const token = options.token ?? getNousToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  if (options.signal)
    options.signal.addEventListener("abort", () => controller.abort(), { once: true });
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      ...options,
      headers,
      credentials: "include",
      signal: controller.signal,
    });
  } catch (error) {
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
