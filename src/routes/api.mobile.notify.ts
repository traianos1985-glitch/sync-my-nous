import { createFileRoute } from "@tanstack/react-router";
import { randomUUID } from "node:crypto";
import { createJob } from "../lib/db/jobs";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { NOUS_LIMITS } from "../lib/platform-policy";

export const Route = createFileRoute("/api/mobile/notify")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as Record<string, unknown>;
        const deviceId =
          typeof body["deviceId"] === "string" ? body["deviceId"].trim().slice(0, 160) : "";
        const title = typeof body["title"] === "string" ? body["title"].trim().slice(0, 120) : "";
        const message =
          typeof body["message"] === "string" ? body["message"].trim().slice(0, 500) : "";
        if (!deviceId || !title || !message)
          return Response.json(
            { error: "deviceId, title and message are required" },
            { status: 400 },
          );
        const job = await createJob(userId, "mobile_notification", {
          deliveryId: randomUUID(),
          deviceId,
          title,
          message,
          priority: body["priority"] === "high" ? "high" : "normal",
          maxAttempts: NOUS_LIMITS.maxJobRetries,
        });
        return Response.json(
          { ok: true, delivery: { id: job.id, status: job.status, queuedAt: job.createdAt } },
          { status: 202 },
        );
      },
    },
  },
});
