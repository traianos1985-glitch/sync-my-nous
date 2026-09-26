import { createFileRoute } from "@tanstack/react-router";
import { sql } from "drizzle-orm";
import { db } from "../lib/db";

export const Route = createFileRoute("/api/health")({
  server: {
    handlers: {
      GET: async () => {
        const startedAt = performance.now();
        try {
          await db.execute(sql`SELECT 1`);
          return Response.json({
            ok: true,
            status: "healthy",
            checks: { database: "ok" },
            latencyMs: Math.round(performance.now() - startedAt),
            timestamp: new Date().toISOString(),
          });
        } catch {
          return Response.json(
            {
              ok: false,
              status: "degraded",
              checks: { database: "failed" },
              latencyMs: Math.round(performance.now() - startedAt),
              timestamp: new Date().toISOString(),
            },
            { status: 503 },
          );
        }
      },
    },
  },
});
