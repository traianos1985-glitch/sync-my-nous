import { createFileRoute } from "@tanstack/react-router";
import { processNextMobileDelivery } from "../lib/mobile-delivery";

function isAuthorized(request: Request) {
  const expected = process.env["NOUS_WORKER_TOKEN"];
  return Boolean(expected && request.headers.get("authorization") === `Bearer ${expected}`);
}

export const Route = createFileRoute("/api/mobile/worker")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        if (!isAuthorized(request))
          return Response.json({ error: "Unauthorized" }, { status: 401 });
        const body = (await request.json()) as { userId?: unknown };
        if (typeof body.userId !== "string" || !body.userId)
          return Response.json({ error: "userId is required" }, { status: 400 });
        return Response.json({ ok: true, result: await processNextMobileDelivery(body.userId) });
      },
    },
  },
});
