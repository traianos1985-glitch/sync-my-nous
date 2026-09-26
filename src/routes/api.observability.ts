import { createFileRoute } from "@tanstack/react-router";
import { desc, eq } from "drizzle-orm";
import { db } from "../lib/db";
import { nousObservabilityEvents } from "../lib/db/schema";
import { getModelCallMetrics } from "../lib/ai-observability";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/observability")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const events = await db
          .select()
          .from(nousObservabilityEvents)
          .where(eq(nousObservabilityEvents.userId, userId))
          .orderBy(desc(nousObservabilityEvents.createdAt))
          .limit(100);
        return Response.json({ ok: true, model: getModelCallMetrics(), events });
      },
    },
  },
});
