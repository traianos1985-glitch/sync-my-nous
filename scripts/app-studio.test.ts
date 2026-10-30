import { afterEach, expect, test } from "bun:test";
import {
  fileTree,
  canApproveRepair,
  appendConsole,
  type RepairDetail,
} from "../src/components/nous/app-studio-model";
import { runStudioValidation } from "../src/lib/app-studio-api";
import { nousBlob } from "../src/lib/nous-api";
const original = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = original;
});

test("explorer retains nested generated files and rejects traversal", () => {
  const nodes = fileTree([
    { name: "tests/test_main.py", size: 42 },
    { name: "main.py", size: 20 },
    { name: "../secrets", size: 1 },
  ]);
  expect(nodes).toHaveLength(2);
  expect(nodes[0].children[0].file?.name).toBe("tests/test_main.py");
});
test("repair approval requires a pending proposal and clear preflight", () => {
  const detail: RepairDetail = {
    ok: true,
    proposal: { repair_id: "one", app_name: "sample", status: "pending_review", summary: "Fix" },
    review: { ready_for_human_review: true, blockers: [], warnings: [] },
    changes: [],
  };
  expect(canApproveRepair(detail)).toBe(true);
  expect(
    canApproveRepair({ ...detail, review: { ...detail.review, blockers: ["stale_baseline"] } }),
  ).toBe(false);
  expect(canApproveRepair({ ...detail, proposal: { ...detail.proposal, status: "applied" } })).toBe(
    false,
  );
  expect(canApproveRepair(null)).toBe(false);
});
test("console retains the newest bounded output", () => {
  expect(appendConsole("x".repeat(24_000), "last")).toHaveLength(24_000);
  expect(appendConsole("x".repeat(24_000), "last").endsWith("last")).toBe(true);
});
test("live validation reads split SSE output and failed terminal result without replay", async () => {
  const requests: string[] = [];
  globalThis.fetch = (async (url, options) => {
    requests.push(String(url));
    expect(options?.method).toBe("POST");
    expect(JSON.parse(String(options?.body))).toEqual({ app_name: "sample", timeout_seconds: 120 });
    return new Response(
      new ReadableStream({
        start(controller) {
          for (const part of [
            'event: output\r\ndata: {"text":"assertion ',
            'failed\\n"}\r\n\r\nevent: result\ndata: {"ok":false,"status":"failed","return_code":1}\n\n',
          ])
            controller.enqueue(new TextEncoder().encode(part));
          controller.close();
        },
      }),
      { headers: { "Content-Type": "text/event-stream" } },
    );
  }) as typeof fetch;
  const output: string[] = [];
  const result = await runStudioValidation("sample", (text) => output.push(text));
  expect(result.status).toBe("failed");
  expect(output).toEqual(["assertion failed\n"]);
  expect(requests).toEqual(["https://nous-ai-os-api.onrender.com/remote/app-builder/test-stream"]);
});
test("incomplete validation never claims success or automatically reruns tests", async () => {
  let calls = 0;
  globalThis.fetch = (async () => {
    calls++;
    return new Response('event: output\ndata: {"text":"partial"}\n\n');
  }) as typeof fetch;
  await expect(runStudioValidation("sample", () => undefined)).rejects.toThrow(
    "Δεν έγινε αυτόματη επανάληψη",
  );
  expect(calls).toBe(1);
});
test("download uses authenticated Render transport without token URL", async () => {
  globalThis.fetch = (async (url, options) => {
    expect(String(url)).toBe(
      "https://nous-ai-os-api.onrender.com/remote/app-builder/download/sample",
    );
    expect(new Headers(options?.headers).get("Accept")).toBe("application/zip");
    return new Response(new Uint8Array([80, 75]));
  }) as typeof fetch;
  expect((await nousBlob("/remote/app-builder/download/sample")).size).toBe(2);
});
