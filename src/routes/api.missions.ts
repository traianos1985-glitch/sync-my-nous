import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { and, eq, desc } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousMissions } from "../lib/db/schema";
import { createExecutionReceipt } from "../lib/execution-receipt";
import { persistExecutionReceipt } from "../lib/receipt-service";

const NOUS_API_FALLBACK = "https://nous-ai-os-api.onrender.com";

// Forward a new mission to the Nous backend on Render so it is actually planned,
// instead of sitting in "queued" forever. Plan only (no execution) — execution
// still goes through the approval flow.
async function dispatchToNous(objective: string): Promise<{ status: string; error?: string }> {
  const token = process.env["NOUS_API_TOKEN"] ?? process.env["NOUS_TOKEN"];
  if (!token) return { status: "queued", error: "NOUS_API_TOKEN not configured" };
  const base = (process.env["NOUS_API_URL"] ?? NOUS_API_FALLBACK).replace(/\/+$/, "");
  try {
    const res = await fetch(`${base}/remote/executive/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-NOUS-TOKEN": token },
      body: JSON.stringify({ prompt: objective.slice(0, 2000) }),
      signal: AbortSignal.timeout(30_000),
    });
    if (!res.ok) {
      const text = await res.text();
      console.error(`Nous dispatch failed [${res.status}]: ${text}`);
      return { status: "failed", error: `Render ${res.status}: ${text.slice(0, 300)}` };
    }
    return { status: "awaiting_approval" };
  } catch (err) {
    console.error("Nous dispatch error", err);
    return { status: "failed", error: String(err) };
  }
}

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
        const uid = await userId(request);
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
          .where(and(eq(nousMissions.id, body.id), eq(nousMissions.userId, uid)))
          .returning();
        return mission
          ? Response.json({ mission })
          : Response.json({ error: "Mission not found" }, { status: 404 });
      },
      POST: async ({ request }) => {
        const startedAt = new Date().toISOString();
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
        const dispatch = await dispatchToNous(objective);
        if (dispatch.status !== mission.status) {
          await db
            .update(nousMissions)
            .set({ status: dispatch.status, updatedAt: new Date() })
            .where(eq(nousMissions.id, mission.id));
          mission.status = dispatch.status;
        }
        const receipt = createExecutionReceipt({
          id: mission.id,
          operation: "mission",
          startedAt,
          status:
            dispatch.status === "failed"
              ? "failed"
              : dispatch.status === "awaiting_approval"
                ? "awaiting_approval"
                : "queued",
          evidence: {
            provider: "nous-dispatch",
            model: dispatch.status,
            researchUsed: false,
            persisted: true,
          },
        });
        await persistExecutionReceipt(mission.userId, receipt);
        return Response.json(
          {
            ok: true,
            mission,
            dispatch: { error: dispatch.error },
            receipt,
          },
          { status: 201 },
        );
      },
    },
  },
});
