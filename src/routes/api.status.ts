import { createFileRoute } from "@tanstack/react-router";
import { count, desc, eq } from "drizzle-orm";
import { db } from "../lib/db";
import { nousMissions, nousObservabilityEvents, nousToolRuns } from "../lib/db/schema";

function getUserId(request: Request) {
  return request.headers.get("x-nous-user-id")?.slice(0, 128) || "anonymous";
}

export const Route = createFileRoute("/api/status")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = getUserId(request);
        try {
          const [missions, runs, events] = await Promise.all([
            db.select({ value: count() }).from(nousMissions).where(eq(nousMissions.userId, userId)),
            db.select({ value: count() }).from(nousToolRuns).where(eq(nousToolRuns.userId, userId)),
            db
              .select()
              .from(nousObservabilityEvents)
              .where(eq(nousObservabilityEvents.userId, userId))
              .orderBy(desc(nousObservabilityEvents.createdAt))
              .limit(10),
          ]);
          return Response.json({
            ok: true,
            service: "nous",
            status: "online",
            counts: { missions: missions[0]?.value ?? 0, toolRuns: runs[0]?.value ?? 0 },
            recentEvents: events,
          });
        } catch (error) {
          console.warn(
            "[v0] status database unavailable",
            error instanceof Error ? error.message : error,
          );
          return Response.json(
            { ok: false, service: "nous", status: "degraded", storage: "unavailable" },
            { status: 503 },
          );
        }
      },
    },
  },
});
