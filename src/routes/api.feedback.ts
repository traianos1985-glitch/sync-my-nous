import { createFileRoute } from "@tanstack/react-router";
import { and, eq } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousMessageFeedback } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/feedback")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as {
          messageId?: string;
          rating?: "positive" | "negative";
          reason?: string;
          note?: string;
        };
        if (!body.messageId || !body.rating || !["positive", "negative"].includes(body.rating))
          return Response.json({ error: "messageId and rating are required" }, { status: 400 });
        const [feedback] = await db
          .insert(nousMessageFeedback)
          .values({
            id: randomUUID(),
            userId,
            messageId: body.messageId,
            rating: body.rating,
            reason: body.reason?.slice(0, 120),
            note: body.note?.slice(0, 2000),
          })
          .onConflictDoUpdate({
            target: [nousMessageFeedback.userId, nousMessageFeedback.messageId],
            set: {
              rating: body.rating,
              reason: body.reason?.slice(0, 120),
              note: body.note?.slice(0, 2000),
            },
          })
          .returning();
        return Response.json({ ok: true, feedback });
      },
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const messageId = new URL(request.url).searchParams.get("messageId");
        if (!messageId) return Response.json({ error: "messageId is required" }, { status: 400 });
        const [feedback] = await db
          .select()
          .from(nousMessageFeedback)
          .where(
            and(
              eq(nousMessageFeedback.userId, userId),
              eq(nousMessageFeedback.messageId, messageId),
            ),
          )
          .limit(1);
        return Response.json({ ok: true, feedback: feedback ?? null });
      },
    },
  },
});
