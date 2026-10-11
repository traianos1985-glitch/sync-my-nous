const requestWindows = new Map<string, number[]>();

/**
 * Process-local per-user throttle shared by the standard and streaming chat routes.
 * Persistent daily usage is enforced separately by model-observability.
 */
export function allowChatRequest(userId: string): boolean {
  const now = Date.now();
  const recent = (requestWindows.get(userId) ?? []).filter((time) => now - time < 60_000);
  if (recent.length >= 20) return false;
  recent.push(now);
  requestWindows.set(userId, recent);
  return true;
}
