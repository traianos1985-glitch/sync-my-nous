import { expect, test } from "bun:test";
import { mergeToolCall, normalizeToolCalls } from "../src/components/nous/chat-tool-model";
import { normalizeStoredChatMessage } from "../src/components/nous/dashboard-chat-model";

test("tool events replace running state without duplicating execution", () => {
  const call = { id: "one", name: "system_status", status: "running", input: {} };
  const next = mergeToolCall(normalizeToolCalls([call]), { ...call, status: "completed", output: { cpu: 42 } });
  expect(next).toHaveLength(1);
  expect(next[0].status).toBe("completed");
  expect(next[0].output).toEqual({ cpu: 42 });
});
test("sessions retain tool results and do not restore unconfirmed work as running", () => {
  const message = normalizeStoredChatMessage({ id: "m", role: "assistant", text: "done", toolCalls: [
    { id: "one", name: "read_file", status: "completed", input: {path: "note.txt"}, output: "file contents" },
    { id: "two", name: "search_web", status: "running", input: {query: "news"} },
  ] });
  expect(message?.toolCalls?.[0].output).toBe("file contents");
  expect(message?.toolCalls?.[1].status).toBe("interrupted");
});
test("rejects invalid records and caps at backend's three calls", () => {
  expect(normalizeToolCalls([{id: 1, name: "x", status: "completed"}])).toEqual([]);
  expect(normalizeToolCalls(Array.from({length: 5}, (_, i) => ({id: String(i), name: "x", status: "completed"})))).toHaveLength(3);
});