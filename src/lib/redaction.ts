const SENSITIVE_KEY = /token|secret|password|authorization|cookie|api[_-]?key/i;

export function redactForAudit(value: unknown): unknown {
  if (typeof value === "string") {
    return value.replace(
      /(bearer\s+|api[_-]?key\s*[:=]\s*|token\s*[:=]\s*)[^\s,;]+/gi,
      "$1[REDACTED]",
    );
  }
  if (Array.isArray(value)) return value.map(redactForAudit);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [
        key,
        SENSITIVE_KEY.test(key) ? "[REDACTED]" : redactForAudit(child),
      ]),
    );
  }
  return value;
}
