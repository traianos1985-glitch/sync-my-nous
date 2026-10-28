import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Keyboard } from "lucide-react";
import { QUICK_SHORTCUTS } from "./command-menu-model";

export function ShortcutsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const groups: Array<"Πλοήγηση" | "Ενέργειες" | "Γενικά"> = ["Γενικά", "Πλοήγηση", "Ενέργειες"];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl border-border bg-card/95 p-6 backdrop-blur-xl">
        <DialogHeader className="mb-3 flex flex-row items-center gap-3 space-y-0 text-left">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Keyboard className="size-5" />
          </div>
          <div>
            <DialogTitle className="text-base font-semibold text-foreground">
              Συντομεύσεις πληκτρολογίου
            </DialogTitle>
            <p className="text-xs text-muted-foreground">Πλοηγηθείτε ταχύτατα στο NOUS Workspace</p>
          </div>
        </DialogHeader>

        <div className="space-y-3.5">
          {groups.map((group) => {
            const items = QUICK_SHORTCUTS.filter((s) => s.group === group);
            if (items.length === 0) return null;
            return (
              <div key={group} className="space-y-1.5">
                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {group}
                </h4>
                <div className="divide-y divide-border/50 rounded-xl border border-border/70 bg-background/60">
                  {items.map((shortcut) => (
                    <div
                      key={shortcut.key}
                      className="flex items-center justify-between gap-3 px-3 py-2 text-xs"
                    >
                      <span className="text-foreground">{shortcut.description}</span>
                      <kbd className="shrink-0 rounded border border-border bg-muted/50 px-2 py-0.5 font-mono text-[11px] font-semibold text-muted-foreground shadow-sm">
                        {shortcut.key}
                      </kbd>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
