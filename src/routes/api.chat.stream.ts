import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { db } from "../lib/db";
import { nousMessages } from "../lib/db/schema";
import { randomUUID } from "node:crypto";

export const Route = createFileRoute("/api/chat/stream")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as { answer?: string; missionId?: string };
        const answer = body.answer?.trim().slice(0, 20_000) ?? "";
        if (!answer) return Response.json({ error: "Missing answer" }, { status: 400 });

        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          async start(controller) {
            const send = (event: string, data: unknown) => {
              controller.enqueue(
                encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`),
              );
            };
            send("start", { ok: true });
            for (const chunk of answer.match(/.{1,160}(?:\s+|$)/g) ?? [answer]) {
              send("token", { text: chunk });
              await new Promise((resolve) => setTimeout(resolve, 8));
            }
            await db.insert(nousMessages).values({
              id: randomUUID(),
              missionId: body.missionId?.slice(0, 128) ?? null,
              userId,
              role: "assistant",
              content: answer,
              citations: [],
            });
            send("done", { ok: true });
            controller.close();
          },
        });
        return new Response(stream, {
          headers: {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-cache, no-store",
            Connection: "keep-alive",
          },
        });
      },
    },
  },
});
