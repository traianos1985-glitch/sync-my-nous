import { useState } from "react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";

import {
  RotateCcw,
  MessageSquare,
  Check,
  Copy,
  Sparkles,
  Keyboard,
  CheckCircle2,
} from "lucide-react";

import { getNousApiBase } from "@/lib/nous-api";
import { NavGlyph } from "./dashboard-primitives";
import type { useDashboard } from "./use-dashboard";

export function DashboardCommandMenu({
  dashboard,
}: {
  dashboard: ReturnType<typeof useDashboard>;
}) {
  const {
    section,
    commandOpen,
    setCommandOpen,
    setShortcutsOpen,
    chatInputRef,
    loadSystemStatus,
    loadApprovals,
    testGeminiConnection,
    go,
    commandItems,
  } = dashboard;

  const [copiedUrl, setCopiedUrl] = useState(false);

  const copyApiUrl = async () => {
    try {
      await navigator.clipboard.writeText(getNousApiBase());
      setCopiedUrl(true);
      window.setTimeout(() => setCopiedUrl(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  return (
    <CommandDialog open={commandOpen} onOpenChange={setCommandOpen}>
      <CommandInput placeholder="Αναζήτηση στο workspace (ενότητες, ενέργειες, εγκρίσεις)…" />
      <CommandList>
        <CommandEmpty>Δεν βρέθηκε ενότητα ή ενέργεια.</CommandEmpty>

        <CommandGroup heading="Γρήγορες ενέργειες">
          <CommandItem
            value="new message chat νέο μήνυμα"
            onSelect={() => {
              go("chat");
              setCommandOpen(false);
              window.requestAnimationFrame(() => chatInputRef.current?.focus());
            }}
          >
            <MessageSquare className="size-4" />
            <span>Νέο μήνυμα στον NOUS</span>
            <CommandShortcut>↵</CommandShortcut>
          </CommandItem>

          <CommandItem
            value="refresh system health ανανέωση κατάστασης υγείας"
            onSelect={() => {
              void loadSystemStatus();
              setCommandOpen(false);
            }}
          >
            <RotateCcw className="size-4" />
            <span>Ανανέωση health status</span>
          </CommandItem>

          <CommandItem
            value="refresh approvals queue ανανέωση εγκρίσεων"
            onSelect={() => {
              void loadApprovals();
              setCommandOpen(false);
            }}
          >
            <CheckCircle2 className="size-4" />
            <span>Ανανέωση ουράς εγκρίσεων</span>
          </CommandItem>

          <CommandItem
            value="test gemini connection έλεγχος σύνδεσης gemini"
            onSelect={() => {
              void testGeminiConnection();
              setCommandOpen(false);
            }}
          >
            <Sparkles className="size-4" />
            <span>Έλεγχος επικοινωνίας Gemini</span>
          </CommandItem>

          <CommandItem
            value="copy api base url render αντιγραφή διεύθυνσης backend"
            onSelect={() => {
              void copyApiUrl();
            }}
          >
            {copiedUrl ? <Check className="size-4 text-ok" /> : <Copy className="size-4" />}
            <span>{copiedUrl ? "Αντιγράφηκε το API URL!" : "Αντιγραφή διεύθυνσης NOUS API"}</span>
          </CommandItem>

          <CommandItem
            value="keyboard shortcuts συντομεύσεις πληκτρολογίου βοήθεια"
            onSelect={() => {
              setCommandOpen(false);
              setShortcutsOpen(true);
            }}
          >
            <Keyboard className="size-4" />
            <span>Οδηγός συντομεύσεων πληκτρολογίου</span>
            <CommandShortcut>?</CommandShortcut>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Πλοήγηση">
          {commandItems.map((item) => {
            let shortcutText = "";
            if (item.id === "home") shortcutText = "Alt+1";
            else if (item.id === "chat") shortcutText = "Alt+2";
            else if (item.id === "missions") shortcutText = "Alt+3";
            else if (item.id === "approvals") shortcutText = "Alt+4";
            else if (item.id === "settings") shortcutText = "Alt+5";

            return (
              <CommandItem
                key={item.id}
                value={`${item.label} ${item.id}`}
                onSelect={() => {
                  go(item.id);
                  setCommandOpen(false);
                }}
              >
                <NavGlyph name={item.icon} />
                <span>{item.label}</span>
                {item.id === section ? (
                  <CommandShortcut>active</CommandShortcut>
                ) : (
                  shortcutText && <CommandShortcut>{shortcutText}</CommandShortcut>
                )}
              </CommandItem>
            );
          })}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
