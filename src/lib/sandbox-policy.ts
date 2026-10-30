export const SANDBOX_LIMITS = {
  cpuMs: 10_000,
  memoryMb: 256,
  outputBytes: 256_000,
  network: "deny-by-default" as const,
};

const SAFE_COMMANDS = new Set(["node", "python", "python3"]);

export function validateSandboxRequest(input: unknown) {
  if (!input || typeof input !== "object" || Array.isArray(input))
    return { ok: false as const, error: "invalid_request" };
  const value = input as Record<string, unknown>;
  const command = typeof value["command"] === "string" ? value["command"].trim() : "";
  const code = typeof value["code"] === "string" ? value["code"] : "";
  if (!SAFE_COMMANDS.has(command)) return { ok: false as const, error: "command_not_allowed" };
  if (!code || Buffer.byteLength(code, "utf8") > SANDBOX_LIMITS.outputBytes)
    return { ok: false as const, error: "code_too_large" };
  return { ok: true as const, command, code, limits: SANDBOX_LIMITS };
}
