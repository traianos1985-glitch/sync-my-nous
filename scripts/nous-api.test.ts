import { afterEach, describe, expect, test } from "bun:test";
import { nousFetch, NousApiError } from "../src/lib/nous-api";
import {
  REQUEST_TIMEOUT_MS,
  SLOW_REQUEST_MS,
  backendWakeTracker,
  createBackendWakeTracker,
} from "../src/lib/backend-wake-state";

const originalFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = originalFetch;
  backendWakeTracker.reachable();
});
const respond = (status: number, body: unknown = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("Render request safety", () => {
  test("default deadline allows 75 seconds for cold start", () => {
    expect(REQUEST_TIMEOUT_MS).toBe(75_000);
  });
  test("slow indicator starts after four seconds", () => {
    expect(SLOW_REQUEST_MS).toBe(4_000);
  });
  test("requests go directly to Render, including health mapping and query", async () => {
    let url = "";
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      url = String(input);
      return respond(200, { ok: true });
    }) as typeof fetch;
    expect(await nousFetch("/api/health?probe=1")).toEqual({ ok: true });
    expect(url).toBe("https://nous-ai-os-api.onrender.com/health?probe=1");
  });
  for (const status of [502, 503, 504]) {
    test(`GET retries ${status} once`, async () => {
      let calls = 0;
      globalThis.fetch = (async () =>
        respond(++calls === 1 ? status : 200, { ok: true })) as typeof fetch;
      expect(await nousFetch("/health")).toEqual({ ok: true });
      expect(calls).toBe(2);
    });
  }
  for (const method of ["POST", "PATCH", "DELETE"]) {
    test(`${method} never replays a failed mutation`, async () => {
      let calls = 0;
      globalThis.fetch = (async () => {
        calls += 1;
        return respond(503);
      }) as typeof fetch;
      await expect(nousFetch("/remote/action", { method })).rejects.toBeInstanceOf(NousApiError);
      expect(calls).toBe(1);
    });
  }
  test("pre-aborted caller never starts a request", async () => {
    let calls = 0;
    globalThis.fetch = (async () => {
      calls++;
      return respond(200);
    }) as typeof fetch;
    const controller = new AbortController();
    controller.abort();
    await expect(nousFetch("/health", { signal: controller.signal })).rejects.toMatchObject({
      name: "AbortError",
    });
    expect(calls).toBe(0);
    expect(backendWakeTracker.getSnapshot().pending).toBe(0);
  });
  test("cancelling retry delay prevents the second request", async () => {
    let calls = 0;
    const controller = new AbortController();
    globalThis.fetch = (async () => {
      calls++;
      setTimeout(() => controller.abort(), 20);
      return respond(503);
    }) as typeof fetch;
    await expect(nousFetch("/health", { signal: controller.signal })).rejects.toMatchObject({
      name: "AbortError",
    });
    expect(calls).toBe(1);
    expect(backendWakeTracker.getSnapshot().pending).toBe(0);
  });
  test("deadline covers JSON body consumption and cleans up pending state", async () => {
    globalThis.fetch = (async (_input, options) =>
      ({
        ok: true,
        status: 200,
        json: () =>
          new Promise((_resolve, reject) =>
            options?.signal?.addEventListener("abort", () => reject(options.signal?.reason), {
              once: true,
            }),
          ),
      }) as Response) as typeof fetch;
    await expect(nousFetch("/health", { timeoutMs: 20 })).rejects.toMatchObject({ status: 408 });
    expect(backendWakeTracker.getSnapshot().pending).toBe(0);
  });
  test("authentication failure clears stale gateway wake state without retry", async () => {
    backendWakeTracker.gatewayFailure();
    backendWakeTracker.gatewayFailure();
    globalThis.fetch = (async () => respond(401)) as typeof fetch;
    await expect(nousFetch("/health")).rejects.toMatchObject({ status: 401 });
    expect(backendWakeTracker.getSnapshot().phase).toBe("idle");
  });
  test("rejects external or protocol-relative paths", async () => {
    for (const path of [
      "https://other.example/path",
      "//other.example/path",
      "/\\other.example/path",
    ]) {
      await expect(nousFetch(path)).rejects.toThrow("Invalid NOUS API path");
    }
  });
});

describe("concurrent wake state", () => {
  test("one completed request cannot hide another slow request", () => {
    const tracker = createBackendWakeTracker();
    const first = tracker.begin();
    const second = tracker.begin();
    tracker.markSlow(first);
    tracker.markSlow(second);
    tracker.finish(first);
    expect(tracker.getSnapshot()).toMatchObject({ phase: "waiting", pending: 1, slow: 1 });
    tracker.finish(second);
    expect(tracker.getSnapshot()).toMatchObject({ phase: "idle", pending: 0, slow: 0 });
  });
  test("two gateway responses show recovery, reachable response resets it", () => {
    const tracker = createBackendWakeTracker();
    tracker.gatewayFailure();
    expect(tracker.getSnapshot().phase).toBe("idle");
    tracker.gatewayFailure();
    expect(tracker.getSnapshot().phase).toBe("recovering");
    tracker.reachable();
    expect(tracker.getSnapshot().phase).toBe("idle");
  });
  test("finished requests cannot become slow later", () => {
    const tracker = createBackendWakeTracker();
    const id = tracker.begin();
    tracker.finish(id);
    tracker.markSlow(id);
    expect(tracker.getSnapshot().slow).toBe(0);
  });
  test("unsubscribed listeners are not notified", () => {
    const tracker = createBackendWakeTracker();
    let count = 0;
    const unsubscribe = tracker.subscribe(() => count++);
    tracker.begin();
    unsubscribe();
    tracker.begin();
    expect(count).toBe(1);
  });
});
