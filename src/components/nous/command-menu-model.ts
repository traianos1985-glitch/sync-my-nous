export type CommandShortcutInfo = {
  key: string;
  description: string;
  group: "Πλοήγηση" | "Ενέργειες" | "Γενικά";
};

export const QUICK_SHORTCUTS: CommandShortcutInfo[] = [
  { key: "⌘K / Ctrl+K", description: "Άνοιγμα γραμμής εντολών και αναζήτησης", group: "Γενικά" },
  { key: "?", description: "Προβολή οδηγού συντομεύσεων πληκτρολογίου", group: "Γενικά" },
  { key: "Esc", description: "Κλείσιμο διαλόγων και μενού", group: "Γενικά" },
  { key: "Alt+1", description: "Μετάβαση στο Dashboard (Home)", group: "Πλοήγηση" },
  { key: "Alt+2", description: "Μετάβαση στο Chat", group: "Πλοήγηση" },
  { key: "Alt+3", description: "Μετάβαση στις Αποστολές (Missions)", group: "Πλοήγηση" },
  { key: "Alt+4", description: "Μετάβαση στις Εγκρίσεις (Approvals)", group: "Πλοήγηση" },
  { key: "Alt+5", description: "Μετάβαση στις Ρυθμίσεις (Settings)", group: "Πλοήγηση" },
  { key: "↵ (Enter)", description: "Εστίαση στο πεδίο μηνύματος Chat", group: "Ενέργειες" },
];

export function shouldIgnoreKeyboardShortcut(target: EventTarget | null): boolean {
  if (!target || typeof target !== "object") return false;
  const el = target as { tagName?: string; isContentEditable?: boolean };
  const tag = typeof el.tagName === "string" ? el.tagName.toLowerCase() : "";
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  if (el.isContentEditable) return true;
  return false;
}

export function matchSectionShortcut(key: string): string | null {
  switch (key) {
    case "1":
      return "home";
    case "2":
      return "chat";
    case "3":
      return "missions";
    case "4":
      return "approvals";
    case "5":
      return "settings";
    default:
      return null;
  }
}

export type QuickActionItem = {
  id: string;
  label: string;
  description?: string;
  keywords: string[];
  shortcut?: string;
};

export function filterQuickActions(actions: QuickActionItem[], query: string): QuickActionItem[] {
  const q = query.trim().toLowerCase();
  if (!q) return actions;
  return actions.filter(
    (action) =>
      action.label.toLowerCase().includes(q) ||
      action.id.toLowerCase().includes(q) ||
      (action.description && action.description.toLowerCase().includes(q)) ||
      action.keywords.some((k) => k.toLowerCase().includes(q)),
  );
}
