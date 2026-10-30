import { createFileRoute } from "@tanstack/react-router";
import { desc, eq } from "drizzle-orm";
import { randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousObservabilityEvents } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { redactForAudit } from "../lib/redaction";

export const Route = createFileRoute("/api/telemetry")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const events = await db
          .select()
          .from(nousObservabilityEvents)
          .where(eq(nousObservabilityEvents.userId, userId))
          .orderBy(desc(nousObservabilityEvents.createdAt))
          .limit(100);
        return Response.json(
          { ok: true, events },
          { headers: { "Cache-Control": "private, no-store" } },
        );
      },
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as Record<string, unknown>;
        const event = typeof body["event"] === "string" ? body["event"].trim().slice(0, 120) : "";
        if (!event) return Response.json({ error: "event is required" }, { status: 400 });
        const [created] = await db
          .insert(nousObservabilityEvents)
          .values({
            id: randomUUID(),
            userId,
            event,
            provider: typeof body["provider"] === "string" ? body["provider"].slice(0, 80) : null,
            model: typeof body["model"] === "string" ? body["model"].slice(0, 120) : null,
            latencyMs:
              typeof body["latencyMs"] === "number"
                ? Math.max(0, Math.round(body["latencyMs"]))
                : null,
            inputTokens:
              typeof body["inputTokens"] === "number"
                ? Math.max(0, Math.round(body["inputTokens"]))
                : null,
            outputTokens:
              typeof body["outputTokens"] === "number"
                ? Math.max(0, Math.round(body["outputTokens"]))
                : null,
            totalTokens:
              typeof body["totalTokens"] === "number"
                ? Math.max(0, Math.round(body["totalTokens"]))
                : null,
            estimatedCostUsd:
              typeof body["estimatedCostUsd"] === "string"
                ? body["estimatedCostUsd"].slice(0, 40)
                : null,
            metadata: redactForAudit(body["metadata"] ?? {}),
          })
          .returning();
        return Response.json({ ok: true, event: created }, { status: 201 });
      },
    },
  },
});
