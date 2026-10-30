import { createFileRoute } from "@tanstack/react-router";
import { SANDBOX_LIMITS, validateSandboxRequest } from "../lib/sandbox-policy";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

const RUNNER_TIMEOUT_MS = 15_000;

export const Route = createFileRoute("/api/sandbox/run")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        await requireAuthenticatedUserId(request);
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
          return new Response(body, {
            status: response.status,
            headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
          });
        } catch (error) {
          const aborted = error instanceof Error && error.name === "AbortError";
          return Response.json(
            { error: aborted ? "sandbox_runner_timeout" : "sandbox_runner_unavailable" },
            { status: 502 },
          );
        } finally {
          clearTimeout(timeout);
        }
      },
    },
  },
});
