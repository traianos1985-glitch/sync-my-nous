import { describe, expect, it } from "bun:test";
import {
  DEFAULT_WEB_PRESETS,
  cleanSearchQuery,
  createDefaultActions,
  estimateWordCount,
  extractReadText,
  formatJobStatus,
  sanitizeTargetUrl,
} from "../src/components/nous/browser-operator-model";

describe("browser operator model & helpers", () => {
  it("sanitizes target URLs safely", () => {
    expect(sanitizeTargetUrl("")).toBe("");
    expect(sanitizeTargetUrl("   ")).toBe("");
    expect(sanitizeTargetUrl("javascript:alert(1)")).toBe("");
    expect(sanitizeTargetUrl("example.com")).toBe("https://example.com");
    expect(sanitizeTargetUrl("http://internal.service:8080/path")).toBe(
      "http://internal.service:8080/path",
    );
    expect(sanitizeTargetUrl("https://github.com/trending")).toBe("https://github.com/trending");
  });

  it("cleans search queries in Greek and English", () => {
    expect(cleanSearchQuery("ψάξε για quantum computing")).toBe("quantum computing");
    expect(cleanSearchQuery("αναζήτησε στο διαδίκτυο nextjs 15")).toBe("nextjs 15");
    expect(cleanSearchQuery("search for generative ai")).toBe("generative ai");
    expect(cleanSearchQuery("find online python 3.12 release notes")).toBe(
      "python 3.12 release notes",
    );
    expect(cleanSearchQuery("clean query")).toBe("clean query");
  });

  it("formats browser job statuses correctly", () => {
    expect(formatJobStatus("completed")).toEqual({ label: "Ολοκληρώθηκε", tone: "green" });
    expect(formatJobStatus("running")).toEqual({ label: "Εκτελείται", tone: "blue" });
    expect(formatJobStatus("pending")).toEqual({ label: "Σε αναμονή", tone: "yellow" });
    expect(formatJobStatus("failed")).toEqual({ label: "Απέτυχε", tone: "red" });
    expect(formatJobStatus("custom")).toEqual({ label: "custom", tone: "muted" });
    expect(formatJobStatus(undefined)).toEqual({ label: "Άγνωστο", tone: "muted" });
  });

  it("creates default browser actions structure", () => {
    const actions = createDefaultActions("https://mysite.com");
    expect(actions.length).toBe(2);
    expect(actions[0].type).toBe("open");
    expect(actions[0].value).toBe("https://mysite.com");
    expect(actions[1].type).toBe("screenshot");
  });

  it("extracts text from various read result shapes", () => {
    expect(extractReadText("Direct string output")).toBe("Direct string output");
    expect(extractReadText({ content: "Markdown or HTML text" })).toBe("Markdown or HTML text");
    expect(extractReadText({ text: "Plain text field" })).toBe("Plain text field");
    expect(extractReadText({ summary: "Executive summary" })).toBe("Executive summary");
    expect(extractReadText(null)).toBe("");
  });

  it("calculates estimated word counts accurately", () => {
    expect(estimateWordCount("")).toBe(0);
    expect(estimateWordCount("   ")).toBe(0);
    expect(estimateWordCount("Hello world from Nous AI OS")).toBe(6);
    expect(estimateWordCount("Μία δύο τρεις λέξεις")).toBe(4);
  });

  it("contains valid default web presets", () => {
    expect(DEFAULT_WEB_PRESETS.length).toBeGreaterThan(2);
    for (const preset of DEFAULT_WEB_PRESETS) {
      expect(preset.label.length).toBeGreaterThan(0);
      expect(preset.url).toMatch(/^https:\/\//);
      expect(["docs", "news", "api", "bench"]).toContain(preset.category);
    }
  });
});
