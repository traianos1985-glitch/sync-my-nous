export type ChatToolCall = {
  id: string;
  name: string;
  status: "running" | "completed" | "failed" | "blocked" | "interrupted";
  summary: string;
  input: unknown;
  output?: unknown;
  error?: string;
};

function boundedValue(value: unknown): unknown {
  try {
    const encoded = JSON.stringify(value ?? null);
    return encoded.length <= 12000 ? JSON.parse(encoded) : `${encoded.slice(0, 12000)}…`;
  } catch {
    return null;
  }
}

export function normalizeToolCalls(value: unknown, stored = false): ChatToolCall[] {
  if (!Array.isArray(value)) return [];
  return value.slice(0, 3).flatMap((item): ChatToolCall[] => {
    if (
      !item ||
      typeof item !== "object" ||
      typeof item.id !== "string" ||
      typeof item.name !== "string" ||
      !["running", "completed", "failed", "blocked", "interrupted"].includes(item.status)
    )
      return [];
    return [
      {
        id: item.id.slice(0, 128),
        name: item.name.slice(0, 80),
        status: stored && item.status === "running" ? "interrupted" : item.status,
        summary: typeof item.summary === "string" ? item.summary.slice(0, 300) : "",
        input: boundedValue(item.input),
        output: boundedValue(item.output),
        error: typeof item.error === "string" ? item.error.slice(0, 500) : undefined,
      },
    ];
  });
}

export function mergeToolCall(calls: ChatToolCall[], value: unknown): ChatToolCall[] {
  const next = normalizeToolCalls([value])[0];
  if (!next) return calls;
  return calls.some((c) => c.id === next.id)
    ? calls.map((c) => (c.id === next.id ? next : c))
    : [...calls, next].slice(0, 3);
}
