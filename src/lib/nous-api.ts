export type NousApiOptions = RequestInit & { token?: string };

const apiBase = import.meta.env.VITE_NOUS_API_URL ?? "";
const apiToken = import.meta.env.VITE_NOUS_API_TOKEN;

export function hasConfiguredNousApi(): boolean {
  return Boolean(apiBase || apiToken);
}

export async function nousStream(path: string, options: NousApiOptions = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "text/event-stream");
  const token = options.token ?? apiToken;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
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
  const token = options.token ?? apiToken;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error ?? `NOUS API request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}
