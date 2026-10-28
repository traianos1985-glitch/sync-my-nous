import { describe, expect, it } from "bun:test";
import {
  exportChatAsMarkdown,
  exportChatAsJson,
  type ChatMessage,
} from "../src/components/nous/dashboard-chat-model";

describe("chat export formatting", () => {
  const sampleMessages: ChatMessage[] = [
    {
      id: "1",
      role: "user",
      text: "Πώς συνδέεται το backend;",
    },
    {
      id: "2",
      role: "assistant",
      text: "Μέσω του direct Render API base URL.",
      citations: [
        {
          title: "Render Docs",
          url: "https://render.com/docs",
          domain: "render.com",
        },
      ],
    },
  ];

  it("exports markdown with roles, text, citations, and conversation metadata", () => {
    const md = exportChatAsMarkdown(sampleMessages, "42");
    expect(md).toContain("# NOUS Chat Export");
    expect(md).toContain("**ID Συνομιλίας:** 42");
    expect(md).toContain("**Σύνολο μηνυμάτων:** 2");
    expect(md).toContain("### Χρήστης");
    expect(md).toContain("Πώς συνδέεται το backend;");
    expect(md).toContain("### NOUS");
    expect(md).toContain("Μέσω του direct Render API base URL.");
    expect(md).toContain("[Render Docs](https://render.com/docs) (render.com)");
  });

  it("exports valid json with structured messages", () => {
    const raw = exportChatAsJson(sampleMessages, "42");
    const parsed = JSON.parse(raw);
    expect(parsed.conversationId).toBe("42");
    expect(parsed.messageCount).toBe(2);
    expect(parsed.messages).toHaveLength(2);
    expect(parsed.messages[0].role).toBe("user");
    expect(parsed.messages[1].role).toBe("assistant");
    expect(parsed.messages[1].citations[0].domain).toBe("render.com");
  });
});
