import { describe, expect, test } from "bun:test";
import { normalizeSessions, searchSessions } from "../src/components/nous/chat-sessions-model";

describe("browser session records", () => {
  test("keeps multiple independent sessions and conversation IDs", () => {
    const sessions = normalizeSessions([
      {
        id: "one",
        title: "First",
        conversationId: "123",
        messages: [{ id: "m1", role: "user", text: "first question" }],
      },
      {
        id: "two",
        title: "Second",
        conversationId: "456",
        messages: [{ id: "m2", role: "user", text: "second question" }],
      },
    ]);
    expect(sessions).toHaveLength(2);
    expect(sessions[0].messages[0].text).toBe("first question");
    expect(sessions[1].messages[0].text).toBe("second question");
    expect(sessions[1].conversationId).toBe("456");
  });
  test("searches saved session content and renamed titles", () => {
    const sessions = normalizeSessions([
      {
        id: "one",
        title: "Research",
        messages: [{ id: "m", role: "user", text: "SQLite durability" }],
      },
      { id: "two", title: "Travel", messages: [] },
    ]);
    expect(searchSessions(sessions, "sqlite").map((s) => s.id)).toEqual(["one"]);
    expect(searchSessions(sessions, "travel").map((s) => s.id)).toEqual(["two"]);
  });
});
