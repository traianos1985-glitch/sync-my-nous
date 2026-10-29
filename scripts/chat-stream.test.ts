import { afterEach, expect, test } from "bun:test";
import { requestChat } from "../src/lib/nous-chat-stream";

const original = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = original;
});

test("reads split tool events and final result in one POST", async () => {
  let requests = 0;
  const encoder = new TextEncoder();
  globalThis.fetch = (async () => {
    requests++;
    return new Response(
      new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('event: tool\ndata: {"id":"one","status":"run'));
          controller.enqueue(
            encoder.encode('ning"}\n\nevent: result\ndata: {"answer":"done"}\n\n'),
          );
          controller.close();
        },
      }),
      { headers: { "Content-Type": "text/event-stream" } },
    );
  }) as typeof fetch;
  const calls: unknown[] = [];
  const result = await requestChat(
    { message: "system status" },
    new AbortController().signal,
    (c) => calls.push(c),
  );
  expect(result).toEqual({ answer: "done" });
  expect(calls).toEqual([{ id: "one", status: "running" }]);
  expect(requests).toBe(1);
});

test("older JSON backend is read without replaying chat", async () => {
  let requests = 0;
  globalThis.fetch = (async () => {
    requests++;
    return new Response('{"answer":"legacy"}', { headers: { "Content-Type": "application/json" } });
  }) as typeof fetch;
  expect(await requestChat({}, new AbortController().signal, () => {})).toEqual({
    answer: "legacy",
  });
  expect(requests).toBe(1);
});

test("partial result fails without replay and keeps delivered tool event", async () => {
  const calls: unknown[] = [];
  globalThis.fetch = (async () =>
    new Response('event: tool\ndata: {"id":"one","status":"completed"}\n\n', {
      headers: { "Content-Type": "text/event-stream" },
    })) as typeof fetch;
  await expect(
    requestChat({}, new AbortController().signal, (c) => calls.push(c)),
  ).rejects.toThrow();
  expect(calls).toHaveLength(1);
});
