import { randomUUID } from "node:crypto";
import { eq, and } from "drizzle-orm";
import { db } from "./index";
import { nousMemoryEntries } from "./schema";

export async function readMemory<T>(userId: string, memoryKey: string, fallback: T): Promise<T> {
  const [entry] = await db
    .select({ value: nousMemoryEntries.value })
    .from(nousMemoryEntries)
    .where(and(eq(nousMemoryEntries.userId, userId), eq(nousMemoryEntries.memoryKey, memoryKey)))
    .limit(1);
  return (entry?.value as T | undefined) ?? fallback;
}

export async function writeMemory(userId: string, memoryKey: string, value: unknown) {
  const now = new Date();
  return db
    .insert(nousMemoryEntries)
    .values({ id: randomUUID(), userId, memoryKey, value, updatedAt: now })
    .onConflictDoUpdate({
      target: [nousMemoryEntries.userId, nousMemoryEntries.memoryKey],
      set: { value, updatedAt: now },
    })
    .returning();
}
