import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { and, eq } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousApprovals, nousMissions, nousToolRuns } from "../lib/db/schema";
import { getToolDefinition } from "../lib/tool-registry";
import { research } from "../lib/research-broker";

async function getUserId(request: Request) {
  return requireAuthenticatedUserId(request);
}

type ApprovalRequest = { approvalId?: unknown };

function parseApprovalRequest(value: unknown): string | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const approvalId = (value as ApprovalRequest).approvalId;
  return typeof approvalId === "string" && approvalId.trim().length > 0 && approvalId.length <= 200
    ? approvalId.trim()
    : null;
}

// Keep this allowlist aligned with the explicit execution branches below. A tool
// appearing in the registry must never be reported as successfully executed
// merely because its execution handler has not been implemented yet.
const EXECUTABLE_APPROVED_TOOLS = new Set(["research", "createMission"]);

export const Route = createFileRoute("/api/tools/execute")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await getUserId(request);

        let body: unknown;
        try {
          body = await request.json();
        } catch {
          return Response.json({ error: "Invalid JSON body" }, { status: 400 });
        }

        const approvalId = parseApprovalRequest(body);
        if (!approvalId) {
          return Response.json({ error: "approvalId must be a non-empty string" }, { status: 400 });
        }

        // Validate the approved action before claiming it. This avoids leaving
        // approvals stuck in "executing" when the tool is unknown or unsupported.
        const [candidate] = await db
          .select()
          .from(nousApprovals)
          .where(
            and(
              eq(nousApprovals.id, approvalId),
              eq(nousApprovals.userId, userId),
              eq(nousApprovals.status, "approved"),
            ),
          )
          .limit(1);

        if (!candidate) {
          return Response.json({ error: "Approved action not found" }, { status: 404 });
        }

        const definition = getToolDefinition(candidate.tool);
        if (!definition || !EXECUTABLE_APPROVED_TOOLS.has(candidate.tool)) {
          return Response.json(
            { error: "Approved tool has no execution handler", tool: candidate.tool },
            { status: 409 },
          );
        }

        const parsed = definition.input.safeParse(candidate.input);
        if (!parsed.success) {
          return Response.json({ error: "Invalid approved tool input" }, { status: 422 });
        }

        // Conditional update is the single-winner claim: simultaneous requests
        // cannot execute the same approval twice.
        const [approval] = await db
          .update(nousApprovals)
          .set({ status: "executing" })
          .where(
            and(
              eq(nousApprovals.id, approvalId),
              eq(nousApprovals.userId, userId),
              eq(nousApprovals.status, "approved"),
            ),
          )
          .returning();

        if (!approval) {
          return Response.json(
            { error: "Approved action is already being handled" },
            { status: 409 },
          );
        }

        const runId = randomUUID();
        if (approval.missionId) {
          await db
            .update(nousMissions)
            .set({ status: "running", updatedAt: new Date() })
            .where(and(eq(nousMissions.id, approval.missionId), eq(nousMissions.userId, userId)));
        }

        try {
          let output: unknown;
          if (approval.tool === "research") {
            output = await research((parsed.data as { query: string }).query, "deep");
          } else if (approval.tool === "createMission") {
            const mission = {
              id: randomUUID(),
              userId,
              title: (parsed.data as { title: string }).title,
              objective: (parsed.data as { objective: string }).objective,
              status: "queued",
            };
            await db.insert(nousMissions).values(mission);
            output = mission;
          } else {
            // Defensive exhaustiveness guard if the allowlist and handlers drift.
            throw new Error("approved_tool_handler_missing");
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
            .where(and(eq(nousApprovals.id, approval.id), eq(nousApprovals.userId, userId)));

          return Response.json({ ok: true, runId, output });
        } catch {
          // Do not return raw provider/exception messages to the browser or
          // persist them in the tool-run payload; they may contain secrets.
          await db.insert(nousToolRuns).values({
            id: runId,
            missionId: approval.missionId,
            userId,
            tool: approval.tool,
            status: "failed",
            input: parsed.data,
            output: { error: "tool_execution_failed" },
          });
          await db
            .update(nousApprovals)
            .set({ status: "failed", resolvedAt: new Date() })
            .where(and(eq(nousApprovals.id, approval.id), eq(nousApprovals.userId, userId)));

          if (approval.missionId) {
            await db
              .update(nousMissions)
              .set({ status: "blocked", updatedAt: new Date() })
              .where(and(eq(nousMissions.id, approval.missionId), eq(nousMissions.userId, userId)));
          }
          return Response.json({ error: "Tool execution failed", runId }, { status: 502 });
        }
      },
    },
  },
});
