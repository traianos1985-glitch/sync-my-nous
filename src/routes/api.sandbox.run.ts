import { createFileRoute } from "@tanstack/react-router";
import { SANDBOX_LIMITS, validateSandboxRequest } from "../lib/sandbox-policy";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { randomUUID } from "node:crypto";
import { createExecutionReceipt } from "../lib/execution-receipt";
import { persistExecutionReceipt } from "../lib/receipt-service";

const RUNNER_TIMEOUT_MS = 15_000;

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
          const body = await response.text();
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
          const receipt = createExecutionReceipt({
            id: receiptId,
            operation: "sandbox",
            startedAt,
            status: "failed",
            evidence: {
              provider: "isolated-sandbox",
              model: aborted ? "timeout" : "unavailable",
              researchUsed: false,
              persisted: true,
            },
          });
          await persistExecutionReceipt(userId, receipt);
          return Response.json(
            { error: aborted ? "sandbox_runner_timeout" : "sandbox_runner_unavailable", receipt },
            { status: 502 },
          );
        } finally {
          clearTimeout(timeout);
        }
      },
    },
  },
});
