import { createFileRoute } from "@tanstack/react-router";
import { eq, desc } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousMissions } from "../lib/db/schema";

function userId(request: Request) {
  return request.headers.get("x-nous-user-id")?.slice(0, 128) || "anonymous";
}

export const Route = createFileRoute("/api/missions")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const missions = await db
          .select()
          .from(nousMissions)
          .where(eq(nousMissions.userId, userId(request)))
          .orderBy(desc(nousMissions.updatedAt))
          .limit(50);
        return Response.json({ ok: true, missions });
      },
      POST: async ({ request }) => {
        const body = (await request.json()) as { title?: string; objective?: string };
        const title = body.title?.trim().slice(0, 160);
        const objective = body.objective?.trim().slice(0, 4000);
        if (!title || !objective)
          return Response.json({ error: "title and objective are required" }, { status: 400 });
        const mission = {
          id: randomUUID(),
          userId: userId(request),
          title,
          objective,
          status: "queued",
        };
        await db.insert(nousMissions).values(mission);
        return Response.json({ ok: true, mission }, { status: 201 });
      },
    },
  },
});
