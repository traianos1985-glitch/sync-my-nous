import test from "node:test";
import assert from "node:assert/strict";
import { validateSandboxRequest } from "../src/lib/sandbox-policy.ts";

test("sandbox denies arbitrary commands", () => {
  assert.equal(validateSandboxRequest({ command: "bash", code: "id" }).ok, false);
});

test("sandbox accepts bounded supported code", () => {
  assert.equal(validateSandboxRequest({ command: "node", code: "console.log(1)" }).ok, true);
});
