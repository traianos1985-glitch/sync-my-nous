import { nousStream } from "./nous-api";

export async function requestChat<T>(
  body: unknown,
  signal: AbortSignal,
  onTool: (value: unknown) => void,
): Promise<T> {
  const deadline = Date.now() + 120000;
  const response = await nousStream("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
    timeoutMs: 120000,
  });
  // Older Render deployments still return JSON. Never replay the POST to negotiate transport.
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Κενή ροή απάντησης.");
  const abort = () => {
    void reader.cancel();
  };
  signal.addEventListener("abort", abort, { once: true });
  let timedOut = false;
  const timeout = setTimeout(() => { timedOut = true; abort(); }, Math.max(0, deadline - Date.now()));
  const streaming = response.headers.get("content-type")?.includes("text/event-stream");
  const decoder = new TextDecoder();
  let buffer = "";
  let result: T | undefined;
  try {
    while (true) {
      signal.throwIfAborted();
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      if (buffer.length > 1000000) throw new Error("Υπερβολικά μεγάλη απάντηση.");
      if (!streaming) continue;
      let boundary = buffer.indexOf("\n\n");
      while (boundary >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const event = frame
          .split("\n")
          .find((l) => l.startsWith("event: "))
          ?.slice(7);
        const raw = frame
          .split("\n")
          .filter((l) => l.startsWith("data: "))
          .map((l) => l.slice(6))
          .join("\n");
        if (raw) {
          const data: unknown = JSON.parse(raw);
          if (event === "tool") onTool(data);
          if (event === "result") result = data as T;
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
    signal.throwIfAborted();
    if (timedOut) throw new Error("Η αναμονή απάντησης έληξε.");
    if (!streaming) return JSON.parse(buffer) as T;
    if (result === undefined) throw new Error("Η ροή διακόπηκε πριν από την τελική απάντηση.");
    return result;
  } finally {
    clearTimeout(timeout);
    signal.removeEventListener("abort", abort);
    void reader.cancel();
  }
}
