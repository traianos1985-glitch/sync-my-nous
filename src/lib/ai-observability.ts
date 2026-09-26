type ModelCallMetric = {
  startedAt: string;
  durationMs: number;
  ok: boolean;
  inputTokens?: number;
  outputTokens?: number;
  totalTokens?: number;
  estimatedCostUsd?: number;
  error?: string;
};

const calls: ModelCallMetric[] = [];
const DAILY_CALL_LIMIT = Number(process.env["NOUS_AI_DAILY_CALL_LIMIT"] ?? 100);
const MODEL_COST_PER_MILLION_INPUT = Number(process.env["NOUS_AI_INPUT_COST_PER_MILLION"] ?? 1);
const MODEL_COST_PER_MILLION_OUTPUT = Number(process.env["NOUS_AI_OUTPUT_COST_PER_MILLION"] ?? 4);

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

export function canStartModelCall() {
  const today = todayKey();
  const count = calls.filter((call) => call.startedAt.startsWith(today)).length;
  return { allowed: count < DAILY_CALL_LIMIT, count, limit: DAILY_CALL_LIMIT };
}

export function recordModelCall(metric: Omit<ModelCallMetric, "estimatedCostUsd">) {
  const estimatedCostUsd =
    ((metric.inputTokens ?? 0) / 1_000_000) * MODEL_COST_PER_MILLION_INPUT +
    ((metric.outputTokens ?? 0) / 1_000_000) * MODEL_COST_PER_MILLION_OUTPUT;
  calls.push({ ...metric, estimatedCostUsd });
  if (calls.length > 5000) calls.splice(0, calls.length - 5000);
}

export function getModelCallMetrics() {
  const today = todayKey();
  const todayCalls = calls.filter((call) => call.startedAt.startsWith(today));
  return {
    ok: true,
    day: today,
    calls: todayCalls,
    summary: {
      count: todayCalls.length,
      failed: todayCalls.filter((call) => !call.ok).length,
      totalTokens: todayCalls.reduce((sum, call) => sum + (call.totalTokens ?? 0), 0),
      estimatedCostUsd: todayCalls.reduce((sum, call) => sum + (call.estimatedCostUsd ?? 0), 0),
      limit: DAILY_CALL_LIMIT,
    },
  };
}

export function resetModelCallMetricsForTests() {
  calls.length = 0;
}

export function modelCallTimeoutMs() {
  return Number(process.env["NOUS_AI_TIMEOUT_MS"] ?? 30_000);
}

export function withTimeout<T>(promise: Promise<T>, timeoutMs: number) {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`model_timeout_${timeoutMs}ms`)), timeoutMs),
    ),
  ]);
}

export type { ModelCallMetric };
