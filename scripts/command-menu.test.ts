import { describe, expect, it } from "bun:test";
import {
  filterQuickActions,
  matchSectionShortcut,
  QUICK_SHORTCUTS,
  shouldIgnoreKeyboardShortcut,
  type QuickActionItem,
} from "../src/components/nous/command-menu-model";

describe("command menu model and shortcuts", () => {
  it("provides valid shortcuts with required properties", () => {
    expect(QUICK_SHORTCUTS.length).toBeGreaterThan(5);
    for (const shortcut of QUICK_SHORTCUTS) {
      expect(shortcut.key).toBeTruthy();
      expect(shortcut.description).toBeTruthy();
      expect(["Πλοήγηση", "Ενέργειες", "Γενικά"]).toContain(shortcut.group);
    }
  });

  it("maps numeric keys to core section IDs", () => {
    expect(matchSectionShortcut("1")).toBe("home");
    expect(matchSectionShortcut("2")).toBe("chat");
    expect(matchSectionShortcut("3")).toBe("missions");
    expect(matchSectionShortcut("4")).toBe("approvals");
    expect(matchSectionShortcut("5")).toBe("settings");
    expect(matchSectionShortcut("9")).toBeNull();
    expect(matchSectionShortcut("k")).toBeNull();
  });

  it("identifies input targets that should ignore global shortcuts", () => {
    expect(shouldIgnoreKeyboardShortcut(null)).toBe(false);

    const inputEl = { tagName: "INPUT", isContentEditable: false } as unknown as EventTarget;
    expect(shouldIgnoreKeyboardShortcut(inputEl)).toBe(true);

    const textareaEl = { tagName: "TEXTAREA", isContentEditable: false } as unknown as EventTarget;
    expect(shouldIgnoreKeyboardShortcut(textareaEl)).toBe(true);

    const selectEl = { tagName: "SELECT", isContentEditable: false } as unknown as EventTarget;
    expect(shouldIgnoreKeyboardShortcut(selectEl)).toBe(true);

    const editableEl = { tagName: "DIV", isContentEditable: true } as unknown as EventTarget;
    expect(shouldIgnoreKeyboardShortcut(editableEl)).toBe(true);

    const buttonEl = { tagName: "BUTTON", isContentEditable: false } as unknown as EventTarget;
    expect(shouldIgnoreKeyboardShortcut(buttonEl)).toBe(false);

    const divEl = { tagName: "DIV", isContentEditable: false } as unknown as EventTarget;
    expect(shouldIgnoreKeyboardShortcut(divEl)).toBe(false);
  });

  it("filters quick actions by label, id, description and keywords", () => {
    const actions: QuickActionItem[] = [
      {
        id: "refresh-health",
        label: "Ανανέωση health status",
        keywords: ["render", "ping", "status"],
      },
      { id: "refresh-approvals", label: "Ανανέωση εγκρίσεων", keywords: ["pending", "queue"] },
      {
        id: "test-gemini",
        label: "Έλεγχος Gemini",
        description: "Test connection",
        keywords: ["ai", "model"],
      },
    ];

    expect(filterQuickActions(actions, "")).toHaveLength(3);
    expect(filterQuickActions(actions, "health")).toHaveLength(1);
    expect(filterQuickActions(actions, "health")[0].id).toBe("refresh-health");

    // Keyword match
    expect(filterQuickActions(actions, "pending")).toHaveLength(1);
    expect(filterQuickActions(actions, "pending")[0].id).toBe("refresh-approvals");

    // Description match
    expect(filterQuickActions(actions, "connection")).toHaveLength(1);
    expect(filterQuickActions(actions, "connection")[0].id).toBe("test-gemini");

    // No match
    expect(filterQuickActions(actions, "ανύπαρκτο")).toHaveLength(0);
  });
});
