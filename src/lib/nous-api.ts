export type NousApiOptions = RequestInit & { token?: string };

const apiBase = import.meta.env.VITE_NOUS_API_URL ?? "";
const apiToken = import.meta.env.VITE_NOUS_API_TOKEN;

export async function nousFetch<T>(path: string, options: NousApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
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
