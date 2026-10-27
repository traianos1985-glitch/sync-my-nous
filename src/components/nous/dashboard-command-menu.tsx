import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";

import { RotateCcw, MessageSquare } from "lucide-react";

import { NavGlyph } from "./dashboard-primitives";
import type { useDashboard } from "./use-dashboard";

export function DashboardCommandMenu({
  dashboard,
}: {
  dashboard: ReturnType<typeof useDashboard>;
}) {
  const { section, commandOpen, setCommandOpen, chatInputRef, loadSystemStatus, go, commandItems } =
    dashboard;
  return (
    <>
      <CommandDialog open={commandOpen} onOpenChange={setCommandOpen}>
        <CommandInput placeholder="Αναζήτηση στο workspace…" />
        <CommandList>
          <CommandEmpty>Δεν βρέθηκε ενότητα.</CommandEmpty>
          <CommandGroup heading="Πλοήγηση">
            {commandItems.map((item) => (
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
                {item.id === section && <CommandShortcut>active</CommandShortcut>}
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandGroup heading="Γρήγορες ενέργει����ς">
            <CommandItem
              value="new message chat"
              onSelect={() => {
                go("chat");
                setCommandOpen(false);
                window.requestAnimationFrame(() => chatInputRef.current?.focus());
              }}
            >
              <MessageSquare />
              <span>Νέο μήνυμα στον NOUS</span>
              <CommandShortcut>↵</CommandShortcut>
            </CommandItem>
            <CommandItem
              value="refresh system health"
              onSelect={() => {
                void loadSystemStatus();
                setCommandOpen(false);
              }}
            >
              <RotateCcw />
              <span>Ανανέωση health status</span>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  );
}
