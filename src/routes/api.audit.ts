import { createFileRoute } from "@tanstack/react-router";
import { and, desc, eq, gte } from "drizzle-orm";
import { db } from "../lib/db";
import { nousObservabilityEvents } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/audit")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const url = new URL(request.url);
        const format = url.searchParams.get("format") === "csv" ? "csv" : "json";
        const days = Math.min(Math.max(Number(url.searchParams.get("days") ?? 30) || 30, 1), 90);
        const eventFilter = url.searchParams.get("event")?.trim().slice(0, 80) || null;
        const events = await db
          .select()
          .from(nousObservabilityEvents)
          .where(
            and(
              eq(nousObservabilityEvents.userId, userId),
              gte(nousObservabilityEvents.createdAt, new Date(Date.now() - days * 86400000)),
              ...(eventFilter ? [eq(nousObservabilityEvents.event, eventFilter)] : []),
            ),
          )
          .orderBy(desc(nousObservabilityEvents.createdAt))
          .limit(500);

        if (format === "csv") {
          const escape = (value: unknown) => `"${String(value ?? "").replaceAll('"', '""')}"`;
          const csv = [
            ["createdAt", "event", "provider", "model", "latencyMs"],
            ...events.map((event) => [
              event.createdAt.toISOString(),
              event.event,
              event.provider,
              event.model,
              event.latencyMs,
            ]),
          ]
            .map((row) => row.map(escape).join(","))
            .join("\n");
          return new Response(csv, {
            headers: {
              "Content-Type": "text/csv; charset=utf-8",
              "Content-Disposition": `attachment; filename="nous-audit-${new Date().toISOString().slice(0, 10)}.csv"`,
              "Cache-Control": "private, no-store",
            },
          });
        }

        return Response.json(
          {
            ok: true,
            days,
            event: eventFilter,
            count: events.length,
            hasMore: events.length === 500,
            events,
          },
          { headers: { "Cache-Control": "private, no-store" } },
        );
      },
    },
  },
});
