import { createFileRoute } from "@tanstack/react-router";
import { and, count, eq, gte, sql } from "drizzle-orm";
import { db } from "../lib/db";
import { nousMessageFeedback } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/evaluation")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const rows = await db
          .select({ rating: nousMessageFeedback.rating, total: count() })
          .from(nousMessageFeedback)
          .where(eq(nousMessageFeedback.userId, userId))
          .groupBy(nousMessageFeedback.rating);
        const trend = await db
          .select({
            day: sql<string>`to_char(date_trunc('day', ${nousMessageFeedback.createdAt}), 'YYYY-MM-DD')`,
            positive: sql<number>`count(*) filter (where ${nousMessageFeedback.rating} = 'positive')`,
            negative: sql<number>`count(*) filter (where ${nousMessageFeedback.rating} = 'negative')`,
          })
          .from(nousMessageFeedback)
          .where(
            and(
              eq(nousMessageFeedback.userId, userId),
              gte(nousMessageFeedback.createdAt, new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)),
            ),
          )
          .groupBy(sql`date_trunc('day', ${nousMessageFeedback.createdAt})`)
          .orderBy(sql`date_trunc('day', ${nousMessageFeedback.createdAt})`);
        const positive = Number(rows.find((row) => row.rating === "positive")?.total ?? 0);
        const negative = Number(rows.find((row) => row.rating === "negative")?.total ?? 0);
        const total = positive + negative;
        return Response.json(
          {
            ok: true,
            metrics: {
              total,
              positive,
              negative,
              satisfactionRate: total ? Math.round((positive / total) * 100) / 100 : null,
              trend: trend.map((point) => ({
                day: point.day,
                positive: Number(point.positive),
                negative: Number(point.negative),
              })),
            },
          },
          { headers: { "Cache-Control": "private, no-store" } },
        );
      },
    },
  },
});
