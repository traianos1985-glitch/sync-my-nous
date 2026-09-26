import { and, count, eq, gte } from "drizzle-orm";
import { db } from "./db";
import { nousObservabilityEvents } from "./db/schema";
import { recordModelCall, type ModelCallMetric } from "./ai-observability";

export async function recordPersistentModelCall(
  metric: Omit<ModelCallMetric, "estimatedCostUsd">,
  userId: string,
  provider: string,
  model: string,
) {
  recordModelCall(metric);
  const estimatedCostUsd =
    ((metric.inputTokens ?? 0) / 1_000_000) *
      Number(process.env.NOUS_AI_INPUT_COST_PER_MILLION ?? 1) +
    ((metric.outputTokens ?? 0) / 1_000_000) *
      Number(process.env.NOUS_AI_OUTPUT_COST_PER_MILLION ?? 4);
  try {
    await db.insert(nousObservabilityEvents).values({
      id: crypto.randomUUID(),
      userId,
      provider,
      model,
      event: metric.ok ? "model_call" : "model_error",
      latencyMs: metric.durationMs,
      inputTokens: metric.inputTokens,
      outputTokens: metric.outputTokens,
      totalTokens: metric.totalTokens,
      estimatedCostUsd: estimatedCostUsd.toFixed(8),
      metadata: metric.error ? { error: metric.error } : {},
    });
  } catch (error) {
    console.warn(
      "[v0] persistent model observability unavailable",
      error instanceof Error ? error.message : error,
    );
  }
}

export async function getPersistentDailyBudget(userId: string) {
  const start = new Date();
  start.setUTCHours(0, 0, 0, 0);
  const [result] = await db
    .select({ calls: count() })
    .from(nousObservabilityEvents)
    .where(
      and(
        eq(nousObservabilityEvents.userId, userId),
        gte(nousObservabilityEvents.createdAt, start),
      ),
    );
  const used = Number(result?.calls ?? 0);
  const limit = Number(process.env.NOUS_AI_DAILY_CALL_LIMIT ?? 100);
  return { allowed: used < limit, count: used, limit };
}
