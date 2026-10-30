import { describe, expect, test } from "bun:test";
import {
  DEFAULT_MOCK_PRESETS,
  detectEntryFile,
  filterSandboxLogs,
  formatSandboxDuration,
  getViewportWidth,
  hasWebPreview,
} from "../src/components/nous/app-sandbox-model";

describe("app sandbox model & helpers", () => {
  test("detects web preview availability from file list", () => {
    expect(hasWebPreview([])).toBe(false);
    expect(hasWebPreview([{ name: "main.py" }, { name: "requirements.txt" }])).toBe(false);
    expect(hasWebPreview([{ name: "index.html" }, { name: "style.css" }])).toBe(true);
    expect(hasWebPreview([{ name: "public/index.html" }])).toBe(true);
    expect(hasWebPreview([{ name: "dashboard.HTML" }])).toBe(true);
  });

  test("detects entry point file by priority", () => {
    expect(detectEntryFile([])).toBe("none");
    expect(detectEntryFile([{ name: "utils.py" }, { name: "main.py" }])).toBe("main.py");
    expect(detectEntryFile([{ name: "server.py" }, { name: "app.py" }])).toBe("app.py");
    expect(detectEntryFile([{ name: "index.html" }, { name: "app.py" }])).toBe("index.html");
    expect(detectEntryFile([{ name: "script.sh" }])).toBe("script.sh");
  });

  test("returns correct viewport widths", () => {
    expect(getViewportWidth("responsive")).toBe("100%");
    expect(getViewportWidth("desktop")).toBe("1200px");
    expect(getViewportWidth("tablet")).toBe("768px");
    expect(getViewportWidth("mobile")).toBe("375px");
  });

  test("filters sandbox logs by severity", () => {
    const rawLogs = [
      "2026-10-30 08:00:00 [INFO] Server started on port 5000",
      "2026-10-30 08:00:01 [WARNING] Slow query detected",
      "2026-10-30 08:00:02 [ERROR] Connection refused",
      "Traceback (most recent call last):",
      "2026-10-30 08:00:03 [INFO] Request completed 200 OK",
    ].join("\n");

    const all = filterSandboxLogs(rawLogs, "all");
    expect(all.length).toBe(5);

    const errors = filterSandboxLogs(rawLogs, "errors");
    expect(errors.length).toBe(3);
    expect(errors.some((l) => l.includes("Connection refused"))).toBe(true);
    expect(errors.some((l) => l.includes("Traceback"))).toBe(true);
    expect(errors.some((l) => l.includes("Slow query detected"))).toBe(true);

    const info = filterSandboxLogs(rawLogs, "info");
    expect(info.length).toBe(2);
    expect(info.every((l) => !l.includes("ERROR"))).toBe(true);
  });

  test("formats durations properly", () => {
    expect(formatSandboxDuration(undefined)).toBe("—");
    expect(formatSandboxDuration(NaN)).toBe("—");
    expect(formatSandboxDuration(0.045)).toBe("45ms");
    expect(formatSandboxDuration(1.234)).toBe("1.23s");
    expect(formatSandboxDuration(15.0)).toBe("15.00s");
  });

  test("includes default mock presets with valid configurations", () => {
    expect(DEFAULT_MOCK_PRESETS.length).toBeGreaterThanOrEqual(4);
    const health = DEFAULT_MOCK_PRESETS.find((p) => p.name === "Health Check");
    expect(health).toBeDefined();
    expect(health?.method).toBe("GET");
    expect(health?.path).toBe("/");

    const echo = DEFAULT_MOCK_PRESETS.find((p) => p.name === "Echo Data Probe");
    expect(echo).toBeDefined();
    expect(echo?.method).toBe("POST");
    expect(echo?.body).toContain("Hello from NOUS Sandbox");
  });
});
