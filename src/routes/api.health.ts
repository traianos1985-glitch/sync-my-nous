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
          const checks = {
            database: "ok",
            aiGateway:
              process.env["AI_GATEWAY_API_KEY"] || process.env["GCP_API_KEY"]
                ? "configured"
                : "missing",
            research: "available",
          } as const;
          const healthy = checks.aiGateway !== "missing";
          return Response.json(
            {
              ok: healthy,
              status: healthy ? "healthy" : "degraded",
              checks,
              latencyMs: Math.round(performance.now() - startedAt),
              timestamp: new Date().toISOString(),
              uptimeSeconds: Math.round(process.uptime()),
            },
            {
              status: healthy ? 200 : 503,
              headers: { "Cache-Control": "no-store" },
            },
          );
        } catch {
          return Response.json(
            {
              ok: false,
              status: "degraded",
              checks: { database: "failed" },
              latencyMs: Math.round(performance.now() - startedAt),
              timestamp: new Date().toISOString(),
              uptimeSeconds: Math.round(process.uptime()),
            },
            { status: 503 },
          );
        }
      },
    },
  },
});
