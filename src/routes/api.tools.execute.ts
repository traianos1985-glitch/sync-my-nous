import { createFileRoute } from "@tanstack/react-router";
import { and, eq } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousApprovals, nousMissions, nousToolRuns } from "../lib/db/schema";
import { getToolDefinition } from "../lib/tool-registry";
import { research } from "../lib/research-broker";

function getUserId(request: Request) {
  return request.headers.get("x-nous-user-id")?.slice(0, 128) || "anonymous";
}

export const Route = createFileRoute("/api/tools/execute")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = getUserId(request);
        const body = (await request.json()) as { approvalId?: string };
        if (!body.approvalId)
          return Response.json({ error: "approvalId is required" }, { status: 400 });

        const [approval] = await db
          .update(nousApprovals)
          .set({ status: "executing" })
          .where(
            and(
              eq(nousApprovals.id, body.approvalId),
              eq(nousApprovals.userId, userId),
              eq(nousApprovals.status, "approved"),
            ),
          )
          .returning();
        if (!approval)
          return Response.json({ error: "Approved action not found" }, { status: 404 });

        const definition = getToolDefinition(approval.tool);
        if (!definition) return Response.json({ error: "Unknown tool" }, { status: 400 });
        const parsed = definition.input.safeParse(approval.input);
        if (!parsed.success) return Response.json({ error: "Invalid tool input" }, { status: 400 });

        const runId = randomUUID();
        try {
          let output: unknown;
          if (approval.tool === "research") {
            output = await research(parsed.data.query, "deep");
          } else if (approval.tool === "createMission") {
            const mission = {
              id: randomUUID(),
              userId,
              title: parsed.data.title,
              objective: parsed.data.objective,
              status: "queued",
            };
            await db.insert(nousMissions).values(mission);
            output = mission;
          }
          await db.insert(nousToolRuns).values({
            id: runId,
            missionId: approval.missionId,
            userId,
            tool: approval.tool,
            status: "completed",
            input: parsed.data,
            output: output ?? {},
          });
          await db
            .update(nousApprovals)
            .set({ status: "completed", resolvedAt: new Date() })
            .where(eq(nousApprovals.id, approval.id));
          return Response.json({ ok: true, runId, output });
        } catch (error) {
          await db.insert(nousToolRuns).values({
            id: runId,
            missionId: approval.missionId,
            userId,
            tool: approval.tool,
            status: "failed",
            input: parsed.data,
            output: { error: error instanceof Error ? error.message : "tool_failed" },
          });
          await db
            .update(nousApprovals)
            .set({ status: "failed", resolvedAt: new Date() })
            .where(eq(nousApprovals.id, approval.id));
          return Response.json({ error: "Tool execution failed", runId }, { status: 502 });
        }
      },
    },
  },
});
