import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { runDefensiveSentinel } from "../lib/defensive-sentinel";

export const Route = createFileRoute("/api/security-audit")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        await requireAuthenticatedUserId(request);
        return Response.json({ ok: true, mode: "defensive-only", ...runDefensiveSentinel() });
      },
    },
  },
});
