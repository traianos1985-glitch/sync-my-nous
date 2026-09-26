import { createFileRoute } from "@tanstack/react-router";
import { desc, eq } from "drizzle-orm";
import { db } from "../lib/db";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { nousMissions } from "../lib/db/schema";

export const Route = createFileRoute("/api/missions/stream")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const encoder = new TextEncoder();
        let timer: ReturnType<typeof setInterval> | undefined;
        const stream = new ReadableStream({
          async start(controller) {
            const send = async () => {
              const missions = await db
                .select({
                  id: nousMissions.id,
                  title: nousMissions.title,
                  status: nousMissions.status,
                  updatedAt: nousMissions.updatedAt,
                })
                .from(nousMissions)
                .where(eq(nousMissions.userId, userId))
                .orderBy(desc(nousMissions.updatedAt))
                .limit(25);
              controller.enqueue(
                encoder.encode(`event: missions\ndata: ${JSON.stringify({ missions })}\n\n`),
              );
            };
            await send();
            timer = setInterval(() => void send().catch(() => undefined), 3000);
          },
          cancel() {
            if (timer) clearInterval(timer);
          },
        });
        return new Response(stream, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            Connection: "keep-alive",
          },
        });
      },
    },
  },
});
