import { createFileRoute } from "@tanstack/react-router";
import { and, desc, eq } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousApprovals, nousObservabilityEvents } from "../lib/db/schema";
import { getToolDefinition } from "../lib/tool-registry";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

async function userId(request: Request) {
  return requireAuthenticatedUserId(request);
}

export const Route = createFileRoute("/api/approvals")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const approvals = await db
          .select()
          .from(nousApprovals)
          .where(
            and(
              eq(nousApprovals.userId, await userId(request)),
              eq(nousApprovals.status, "pending"),
            ),
          )
          .orderBy(desc(nousApprovals.createdAt))
          .limit(50);
        return Response.json({ ok: true, approvals });
      },
      POST: async ({ request }) => {
        const body = (await request.json()) as {
          tool?: string;
          input?: unknown;
          missionId?: string;
        };
        const tool = body.tool?.trim() ?? "";
        const definition = getToolDefinition(tool);
        if (!definition) return Response.json({ error: "Unknown tool" }, { status: 400 });
        const parsed = definition.input.safeParse(body.input ?? {});
        if (!parsed.success) return Response.json({ error: "Invalid tool input" }, { status: 400 });
        const approval = {
          id: randomUUID(),
          missionId: body.missionId?.slice(0, 128) ?? null,
          userId: await userId(request),
          tool,
          input: parsed.data,
          status: "pending",
        };
        await db.insert(nousApprovals).values(approval);
        return Response.json({ ok: true, approval }, { status: 201 });
      },
      PATCH: async ({ request }) => {
        const body = (await request.json()) as { id?: string; status?: string };
        if (!body.id || !["approved", "rejected"].includes(body.status ?? ""))
          return Response.json({ error: "id and status are required" }, { status: 400 });
        const [approval] = await db
          .update(nousApprovals)
          .set({ status: body.status, resolvedAt: new Date() })
          .where(
            and(
              eq(nousApprovals.id, body.id),
              eq(nousApprovals.userId, userId(request)),
              eq(nousApprovals.status, "pending"),
            ),
          )
          .returning();
        if (!approval)
          return Response.json(
            { error: "Approval not found or already resolved" },
            { status: 404 },
          );
        await db.insert(nousObservabilityEvents).values({
          id: randomUUID(),
          userId: await userId(request),
          event: `approval.${body.status}`,
          metadata: { approvalId: approval.id, tool: approval.tool },
        });
        return Response.json({ ok: true, approval });
      },
    },
  },
});
