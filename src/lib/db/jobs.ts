import { randomUUID } from "node:crypto";
import { and, desc, eq, sql } from "drizzle-orm";
import { db } from "./index";
import { nousJobs } from "./schema";
import { isAllowedJobKind, NOUS_LIMITS, serializedBytes } from "../platform-policy";

export async function createJob(userId: string, kind: string, payload: unknown) {
  if (!isAllowedJobKind(kind) || kind.length > NOUS_LIMITS.maxJobKindLength)
    throw new Error("Unsupported job kind");
  if (serializedBytes(payload) > NOUS_LIMITS.maxToolPayloadBytes)
    throw new Error("Job payload is too large");
  const [job] = await db
    .insert(nousJobs)
    .values({ id: randomUUID(), userId, kind, payload, status: "queued" })
    .returning();
  return job;
}

const JOB_STATUSES = new Set(["queued", "running", "completed", "failed", "cancelled"]);

export async function updateJob(id: string, userId: string, status: string, output?: unknown) {
  if (!JOB_STATUSES.has(status)) throw new Error("Invalid job status");
  const now = new Date();
  const [job] = await db
    .update(nousJobs)
    .set({
      status,
      output: output ?? {},
      startedAt: status === "running" ? now : undefined,
      completedAt: ["completed", "failed", "cancelled"].includes(status) ? now : undefined,
      lastError:
        status === "failed"
          ? String((output as { error?: unknown } | undefined)?.error ?? "Job failed").slice(0, 500)
          : undefined,
      updatedAt: now,
    })
    .where(and(eq(nousJobs.id, id), eq(nousJobs.userId, userId)))
    .returning();
  return job;
}

export async function listJobs(userId: string, limit = 25) {
  return db
    .select()
    .from(nousJobs)
    .where(eq(nousJobs.userId, userId))
    .orderBy(desc(nousJobs.updatedAt))
    .limit(Math.min(Math.max(limit, 1), 50));
}

export async function retryJob(id: string, userId: string) {
  const [job] = await db
    .update(nousJobs)
    .set({
      status: "queued",
      retryCount: sql`${nousJobs.retryCount} + 1`,
      lastError: null,
      completedAt: null,
      updatedAt: new Date(),
    })
    .where(and(eq(nousJobs.id, id), eq(nousJobs.userId, userId), eq(nousJobs.status, "failed")))
    .returning();
  return job;
}

export async function getJob(id: string, userId: string) {
  const [job] = await db
    .select()
    .from(nousJobs)
    .where(and(eq(nousJobs.id, id), eq(nousJobs.userId, userId)))
    .limit(1);
  return job;
}
