import { and, desc, eq } from "drizzle-orm";
import { db } from "./db";
import { nousExecutionReceipts } from "./db/schema";
import type { ExecutionReceipt } from "./execution-receipt";

export async function persistExecutionReceipt(userId: string, receipt: ExecutionReceipt) {
  const [row] = await db
    .insert(nousExecutionReceipts)
    .values({
      id: receipt.id,
      userId,
      operation: receipt.operation,
      status: receipt.status,
      verified: receipt.verified,
      startedAt: new Date(receipt.startedAt),
      completedAt: receipt.completedAt ? new Date(receipt.completedAt) : null,
      evidence: receipt.evidence,
      verification: {},
    })
    .onConflictDoUpdate({
      target: nousExecutionReceipts.id,
      set: {
        status: receipt.status,
        completedAt: new Date(receipt.completedAt),
        evidence: receipt.evidence,
      },
    })
    .returning();
  return row;
}

export async function listExecutionReceipts(userId: string, limit = 50) {\n  return db\n    .select()\n    .from(nousExecutionReceipts)\n    .where(eq(nousExecutionReceipts.userId, userId))\n    .orderBy(desc(nousExecutionReceipts.createdAt))\n    .limit(Math.min(Math.max(limit, 1), 100));\n}\n\nexport async function verifyExecutionReceipt(
  userId: string,
  id: string,
  verification: Record<string, unknown>,
) {
  const [row] = await db
    .update(nousExecutionReceipts)
    .set({
      verified: true,
      verification,
    })
    .where(and(eq(nousExecutionReceipts.id, id), eq(nousExecutionReceipts.userId, userId)))
    .returning();
  return row;
}

export async function getExecutionReceipt(userId: string, id: string) {
  const [row] = await db
    .select()
    .from(nousExecutionReceipts)
    .where(and(eq(nousExecutionReceipts.id, id), eq(nousExecutionReceipts.userId, userId)))
    .limit(1);
  return row;
}
