import test from "node:test";
import assert from "node:assert/strict";
import { createExecutionReceipt } from "../src/lib/execution-receipt.ts";

test("approval-pending receipts do not claim completion", () => {
  const receipt = createExecutionReceipt({
    id: "mission-1",
    operation: "mission",
    startedAt: "2026-10-30T10:00:00.000Z",
    status: "awaiting_approval",
    evidence: {
      provider: "nous-dispatch",
      model: "awaiting_approval",
      researchUsed: false,
      persisted: true,
    },
  });
  assert.equal(receipt.status, "awaiting_approval");
  assert.equal(receipt.completedAt, null);
  assert.equal(receipt.verified, false);
});

test("completed receipts include a completion timestamp", () => {
  const receipt = createExecutionReceipt({
    id: "tool-1",
    operation: "tool",
    startedAt: "2026-10-30T10:00:00.000Z",
    evidence: {
      provider: "tool-registry",
      model: "research",
      researchUsed: true,
      persisted: true,
    },
  });
  assert.equal(receipt.status, "completed");
  assert.equal(typeof receipt.completedAt, "string");
});
