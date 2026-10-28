import { useEffect, useState, useSyncExternalStore } from "react";
import { Loader2, RotateCcw, Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import { backendWakeTracker, idleBackendWakeState } from "@/lib/backend-wake-state";

function WakeTimer() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setSeconds((s) => s + 1), 1_000);
    return () => window.clearInterval(timer);
  }, []);
  return <span className="font-mono text-[11px] opacity-80">({seconds}s)</span>;
}

export function BackendWakeBanner({ onRetry }: { onRetry: () => void }) {
  const state = useSyncExternalStore(
    backendWakeTracker.subscribe,
    backendWakeTracker.getSnapshot,
    () => idleBackendWakeState,
  );
  if (state.phase === "idle") return null;
  const waiting = state.pending > 0;

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex shrink-0 flex-wrap items-center gap-3 border-b border-warn/30 bg-warn/10 px-4 py-3 text-warn"
    >
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md border border-warn/30">
        {waiting ? (
          <Loader2 aria-hidden="true" className="size-4 motion-safe:animate-spin" />
        ) : (
          <Server aria-hidden="true" className="size-4" />
        )}
      </div>
      <div className="min-w-0 flex-1 text-xs">
        <p className="flex items-center gap-2 font-semibold">
          <span>{waiting ? "Αναμονή για τον NOUS" : "Το Render δεν είναι ακόμη διαθέσιμο"}</span>
          {waiting && <WakeTimer />}
        </p>
        <p className="mt-1 text-muted-foreground">
          {waiting
            ? "Ο διακομιστής στο Render εκκινείται (cold start). Τα αιτήματά σου παραμένουν ενεργά και θα απαντήσουν αυτόματα μόλις είναι έτοιμος."
            : "Η σύνδεση απέτυχε προσωρινά. Έλεγξε ξανά πριν επαναλάβεις κάποια ενέργεια."}
        </p>
      </div>
      {!waiting && (
        <Button variant="outline" size="sm" onClick={onRetry} className="border-warn/40 text-warn">
          <RotateCcw className="size-3.5" />
          Έλεγχος σύνδεσης
        </Button>
      )}
    </div>
  );
}
