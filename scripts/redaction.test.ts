import test from "node:test";
import assert from "node:assert/strict";
import { redactForAudit } from "../src/lib/redaction.ts";

test("redacts credential-shaped keys recursively", () => {
  const result = redactForAudit({
    token: "secret",
    nested: { password: "pw", safe: "ok" },
  }) as Record<string, unknown>;
  assert.equal(result.token, "[REDACTED]");
  assert.deepEqual(result.nested, { password: "[REDACTED]", safe: "ok" });
});

test("redacts bearer tokens in strings", () => {
  assert.equal(redactForAudit("Authorization: Bearer abc123"), "Authorization: Bearer [REDACTED]");
});
