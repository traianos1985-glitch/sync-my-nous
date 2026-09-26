import { randomUUID } from "node:crypto";
import { and, eq } from "drizzle-orm";
import { db } from "./index";
import { nousJobs } from "./schema";

export async function createJob(userId: string, kind: string, payload: unknown) {
  const [job] = await db
    .insert(nousJobs)
    .values({ id: randomUUID(), userId, kind, payload, status: "queued" })
    .returning();
  return job;
}

export async function updateJob(id: string, userId: string, status: string, output?: unknown) {
  const [job] = await db
    .update(nousJobs)
    .set({ status, output: output ?? {}, updatedAt: new Date() })
    .where(and(eq(nousJobs.id, id), eq(nousJobs.userId, userId)))
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
