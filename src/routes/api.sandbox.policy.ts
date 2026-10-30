import { createFileRoute } from "@tanstack/react-router";
import { SANDBOX_LIMITS, validateSandboxRequest } from "../lib/sandbox-policy";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/sandbox/policy")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        await requireAuthenticatedUserId(request);
        return Response.json({ ok: true, limits: SANDBOX_LIMITS, network: ["deny-by-default"] });
      },
      POST: async ({ request }) => {
        await requireAuthenticatedUserId(request);
        const result = validateSandboxRequest(await request.json());
        return Response.json(result, { status: result.ok ? 200 : 400 });
      },
    },
  },
});
