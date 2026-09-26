export const NOUS_LIMITS = {
  maxToolPayloadBytes: 128_000,
  maxResearchSources: 8,
  maxResearchSeconds: 45,
  maxJobKindLength: 80,
  maxConversationMessages: 40,
  maxJobRetries: 3,
} as const;

export const JOB_KINDS = [
  "knowledge.ingest",
  "knowledge.process",
  "research.run",
  "document.ocr",
  "security.scan",
] as const;

export type NousJobKind = (typeof JOB_KINDS)[number];

export function isAllowedJobKind(kind: string): kind is NousJobKind {
  return JOB_KINDS.includes(kind as NousJobKind);
}

export function serializedBytes(value: unknown) {
  return new TextEncoder().encode(JSON.stringify(value ?? {})).byteLength;
}

export function redactSecrets(value: unknown): unknown {
  if (typeof value === "string") {
    return value.replace(
      /(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+/gi,
      "$1=[REDACTED]",
    );
  }
  if (Array.isArray(value)) return value.map(redactSecrets);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) =>
        /key|token|secret|password|authorization/i.test(key)
          ? [key, "[REDACTED]"]
          : [key, redactSecrets(entry)],
      ),
    );
  }
  return value;
}

export function researchBudget(mode: "auto" | "deep" | "off" = "auto") {
  if (mode === "deep")
    return {
      sources: NOUS_LIMITS.maxResearchSources,
      timeoutMs: NOUS_LIMITS.maxResearchSeconds * 1000,
    };
  if (mode === "off") return { sources: 0, timeoutMs: 0 };
  return { sources: 4, timeoutMs: 20_000 };
}

export function safeErrorMessage(error: unknown) {
  return error instanceof Error ? error.message.slice(0, 500) : "Unknown error";
}
