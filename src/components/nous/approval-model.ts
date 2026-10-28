export type PendingApproval = { id: string; tool: string; input: unknown; createdAt: string };

export function formatApprovalPayload(input: unknown): string {
  if (input === null || input === undefined) return "—";
  if (typeof input === "string") return input;
  try {
    return JSON.stringify(input, null, 2);
  } catch {
    return String(input);
  }
}
