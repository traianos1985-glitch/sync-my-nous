import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { eq, desc } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousMissions } from "../lib/db/schema";

async function userId(request: Request) {
  return requireAuthenticatedUserId(request);
}

export const Route = createFileRoute("/api/missions")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const missions = await db
          .select()
          .from(nousMissions)
          .where(eq(nousMissions.userId, await userId(request)))
          .orderBy(desc(nousMissions.updatedAt))
          .limit(50);
        return Response.json({ ok: true, missions });
      },
      PATCH: async ({ request }) => {
        const userId = getUserId(request);
        const body = (await request.json()) as { id?: string; status?: string };
        const allowed = [
          "queued",
          "planning",
          "awaiting_approval",
          "running",
          "completed",
          "failed",
          "cancelled",
        ];
        if (!body.id || !body.status || !allowed.includes(body.status))
          return Response.json({ error: "Invalid mission transition" }, { status: 400 });
        const [mission] = await db
          .update(nousMissions)
          .set({ status: body.status, updatedAt: new Date() })
          .where(and(eq(nousMissions.id, body.id), eq(nousMissions.userId, userId)))
          .returning();
        return mission
          ? Response.json({ mission })
          : Response.json({ error: "Mission not found" }, { status: 404 });
      },
      POST: async ({ request }) => {
        const body = (await request.json()) as { title?: string; objective?: string };
        const title = body.title?.trim().slice(0, 160);
        const objective = body.objective?.trim().slice(0, 4000);
        if (!title || !objective)
          return Response.json({ error: "title and objective are required" }, { status: 400 });
        const mission = {
          id: randomUUID(),
          userId: await userId(request),
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
