import { createFileRoute } from "@tanstack/react-router";
import { and, desc, eq } from "drizzle-orm";
import { createHash, randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousDevices } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

const deviceInput = (body: unknown) => {
  if (!body || typeof body !== "object" || Array.isArray(body)) return null;
  const value = body as Record<string, unknown>;
  const deviceId =
    typeof value["deviceId"] === "string" ? value["deviceId"].trim().slice(0, 160) : "";
  if (!deviceId) return null;
  return {
    deviceId,
    platform: typeof value["platform"] === "string" ? value["platform"].slice(0, 40) : "android",
    appVersion: typeof value["appVersion"] === "string" ? value["appVersion"].slice(0, 40) : null,
    pushTokenHash:
      typeof value["pushToken"] === "string" && value["pushToken"]
        ? createHash("sha256").update(value["pushToken"]).digest("hex")
        : null,
  };
};

export const Route = createFileRoute("/api/devices")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const devices = await db
          .select({
            id: nousDevices.id,
            deviceId: nousDevices.deviceId,
            platform: nousDevices.platform,
            appVersion: nousDevices.appVersion,
            status: nousDevices.status,
            lastSeenAt: nousDevices.lastSeenAt,
            lastCommandId: nousDevices.lastCommandId,
          })
          .from(nousDevices)
          .where(eq(nousDevices.userId, userId))
          .orderBy(desc(nousDevices.updatedAt));
        return Response.json(
          { ok: true, devices },
          { headers: { "Cache-Control": "private, no-store" } },
        );
      },
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const input = deviceInput(await request.json());
        if (!input) return Response.json({ error: "deviceId is required" }, { status: 400 });
        const now = new Date();
        const [device] = await db
          .insert(nousDevices)
          .values({
            id: randomUUID(),
            userId,
            ...input,
            status: "online",
            lastSeenAt: now,
            updatedAt: now,
          })
          .onConflictDoUpdate({
            target: [nousDevices.userId, nousDevices.deviceId],
            set: { ...input, status: "online", lastSeenAt: now, updatedAt: now },
          })
          .returning();
        return Response.json(
          { ok: true, device },
          { status: 201, headers: { "Cache-Control": "private, no-store" } },
        );
      },
      PATCH: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as {
          deviceId?: string;
          status?: string;
          commandId?: string;
        };
        if (!body.deviceId || !["online", "offline", "degraded"].includes(body.status ?? ""))
          return Response.json(
            { error: "deviceId and valid status are required" },
            { status: 400 },
          );
        const [device] = await db
          .update(nousDevices)
          .set({
            status: body.status,
            lastCommandId: body.commandId?.slice(0, 160) ?? undefined,
            lastSeenAt: new Date(),
            updatedAt: new Date(),
          })
          .where(and(eq(nousDevices.userId, userId), eq(nousDevices.deviceId, body.deviceId)))
          .returning();
        if (!device) return Response.json({ error: "Device not found" }, { status: 404 });
        return Response.json({ ok: true, device });
      },
    },
  },
});
