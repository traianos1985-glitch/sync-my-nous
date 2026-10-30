import { createFileRoute } from "@tanstack/react-router";
import { SANDBOX_LIMITS, validateSandboxRequest } from "../lib/sandbox-policy";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { randomUUID } from "node:crypto";
import { createExecutionReceipt } from "../lib/execution-receipt";
import { persistExecutionReceipt } from "../lib/receipt-service";

const RUNNER_TIMEOUT_MS = 15_000;

async function readBoundedBody(response: Response, maxBytes: number): Promise<string> {
  if (!response.body) return "";
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let total = 0;
  let output = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > maxBytes) {
        await reader.cancel("sandbox output limit exceeded");
        throw new Error("sandbox_output_too_large");
      }
      output += decoder.decode(value, { stream: true });
    }
    return output + decoder.decode();
  } finally {
    reader.releaseLock();
  }
}

export const Route = createFileRoute("/api/sandbox/run")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const startedAt = new Date().toISOString();
        const receiptId = randomUUID();
        const validation = validateSandboxRequest(await request.json());
        if (!validation.ok) return Response.json(validation, { status: 400 });

        const endpoint = process.env["SANDBOX_RUNNER_ENDPOINT"];
        const token = process.env["SANDBOX_RUNNER_TOKEN"];
        if (!endpoint || !token) {
          return Response.json(
            { error: "sandbox_runner_not_configured", limits: SANDBOX_LIMITS },
            { status: 503 },
          );
        }

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), RUNNER_TIMEOUT_MS);
        try {
          const response = await fetch(endpoint, {
            method: "POST",
            signal: controller.signal,
            headers: {
              "content-type": "application/json",
              authorization: `Bearer ${token}`,
              "x-nous-sandbox": "isolated-v1",
            },
            body: JSON.stringify({
              command: validation.command,
              code: validation.code,
              limits: SANDBOX_LIMITS,
            }),
          });
          const body = await readBoundedBody(response, SANDBOX_LIMITS.outputBytes);
          const receipt = createExecutionReceipt({
            id: receiptId,
            operation: "sandbox",
            startedAt,
            status: response.ok ? "completed" : "failed",
            evidence: {
              provider: "isolated-sandbox",
              model: "isolated-v1",
              researchUsed: false,
              persisted: true,
            },
          });
          await persistExecutionReceipt(userId, receipt);
          return Response.json({ result: body, receipt }, { status: response.status });
        } catch (error) {
          const aborted = error instanceof Error && error.name === "AbortError";
          const outputTooLarge = error instanceof Error && error.message === "sandbox_output_too_large";
          const receipt = createExecutionReceipt({
            id: receiptId,
            operation: "sandbox",
            startedAt,
            status: "failed",
            evidence: {
              provider: "isolated-sandbox",
              model: aborted ? "timeout" : outputTooLarge ? "output-limit" : "unavailable",
              researchUsed: false,
              persisted: true,
            },
          });
          await persistExecutionReceipt(userId, receipt);
          return Response.json(
            { error: aborted ? "sandbox_runner_timeout" : outputTooLarge ? "sandbox_output_too_large" : "sandbox_runner_unavailable", receipt },
            { status: 502 },
          );
        } finally {
          clearTimeout(timeout);
        }
      },
    },
  },
});
