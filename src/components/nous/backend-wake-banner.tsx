import { useSyncExternalStore } from "react";
import { Loader2, RotateCcw, Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import { backendWakeTracker, idleBackendWakeState } from "@/lib/backend-wake-state";

export function BackendWakeBanner({ onRetry }: { onRetry: () => void }) {
  const state = useSyncExternalStore(backendWakeTracker.subscribe, backendWakeTracker.getSnapshot, () => idleBackendWakeState);
  if (state.phase === "idle") return null;
  const waiting = state.pending > 0;
  return (
    <div role="status" aria-live="polite" className="flex shrink-0 flex-wrap items-center gap-3 border-b border-warn/30 bg-warn/10 px-4 py-3 text-warn">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md border border-warn/30">
        {waiting ? <Loader2 aria-hidden="true" className="size-4 motion-safe:animate-spin" /> : <Server aria-hidden="true" className="size-4" />}
      </div>
      <div className="min-w-0 flex-1 text-xs">
        <p className="font-semibold">{waiting ? "Αναμονή για τον NOUS" : "Το Render δεν είναι ακόμη διαθέσιμο"}</p>
        <p className="mt-1 text-muted-foreground">{waiting
          ? "Το Render μπορεί να εκκινείται. Τα αιτήματά σου συνεχίζονται — δεν χρειάζεται νέα αποστολή."
          : "Η σύνδεση απέτυχε προσωρινά. Έλεγξε ξανά πριν επαναλάβεις κάποια ενέργεια."}</p>
      </div>
      {!waiting && <Button variant="outline" size="sm" onClick={onRetry} className="border-warn/40 text-warn"><RotateCcw className="size-3.5" />Έλεγχος σύνδεσης</Button>}
    </div>
  );
}
