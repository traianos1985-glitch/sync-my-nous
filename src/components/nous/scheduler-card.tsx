import { useCallback, useEffect, useState } from "react";
import { Check, Copy, HardDrive, Loader2, Timer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getNousApiBase, nousFetch } from "@/lib/nous-api";
import {
  describeTick,
  schedulerCycleUrl,
  storageLabel,
  type ExternalTickResult,
  type StorageReport,
} from "./scheduler-model";

/** Storage durability and 24/7 external scheduler guidance for the Autonomy view. */
export function SchedulerCard({ connected }: { connected: boolean }) {
  const [storage, setStorage] = useState<StorageReport | null>(null);
  const [tick, setTick] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const url = schedulerCycleUrl(getNousApiBase());

  const load = useCallback(async () => {
    try {
      setStorage(await nousFetch<StorageReport>("/api/system/storage"));
    } catch {
      setStorage(null);
    }
  }, []);

  useEffect(() => {
    if (connected) queueMicrotask(load);
  }, [connected, load]);

  async function testTick() {
    setBusy(true);
    try {
      setTick(
        describeTick(
          await nousFetch<ExternalTickResult>("/remote/service/cycle", { method: "POST" }),
        ),
      );
    } catch (err) {
      setTick(err instanceof Error ? err.message : "Αποτυχία");
    } finally {
      setBusy(false);
    }
  }

  async function copyUrl() {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <section className="mt-4 grid gap-4 md:grid-cols-2">
      <div className="rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center gap-2">
          <HardDrive className="size-4 text-primary" />
          <h3 className="font-display text-base font-semibold">Μόνιμη αποθήκευση</h3>
        </div>
        <p className={`mt-3 text-sm font-semibold ${storage?.durable ? "text-ok" : "text-warn"}`}>
          {storageLabel(storage)}
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          {storage?.warning ??
            (storage
              ? "Τα δεδομένα του NOUS διατηρούνται μετά από restart."
              : "Βάλε το NOUS token για να ελεγχθεί ο δίσκος.")}
        </p>
        {storage && !storage.durable && (
          <p className="mt-2 text-xs text-muted-foreground">
            Λύσεις: μόνιμος δίσκος Render (επί πληρωμή) στο /app/data ή εξωτερική βάση δεδομένων.
          </p>
        )}
      </div>
      <div className="rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center gap-2">
          <Timer className="size-4 text-primary" />
          <h3 className="font-display text-base font-semibold">Αυτονομία 24/7</h3>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Η δωρεάν Render κοιμάται μετά από 15 λεπτά. Βάλε στο cron-job.org ένα αίτημα POST κάθε 10
          λεπτά σε αυτή τη διεύθυνση, με header <code>Authorization: Bearer</code> και το NOUS token
          σου. Ο NOUS τρέχει κύκλο μόνο όταν είναι ώρα.
        </p>
        <div className="mt-3 flex min-w-0 items-center gap-2">
          <code className="min-w-0 flex-1 truncate rounded-lg border border-border bg-background px-2 py-1.5 text-[11px]">
            {url}
          </code>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void copyUrl()}
            aria-label="Αντιγραφή διεύθυνσης"
          >
            {copied ? <Check className="size-3.5 text-ok" /> : <Copy className="size-3.5" />}
          </Button>
        </div>
        {storage && !storage.autonomy_enabled_by_default && !storage.durable && (
          <p className="mt-2 text-xs text-warn">
            Σε προσωρινό δίσκο η αυτονομία απενεργοποιείται σε κάθε restart. Όρισε
            NOUS_AUTONOMY_ENABLED_DEFAULT=1 στη Render για να ξεκινά μόνη της.
          </p>
        )}
        <Button
          className="mt-3"
          size="sm"
          variant="outline"
          disabled={!connected || busy}
          onClick={() => void testTick()}
        >
          {busy && <Loader2 className="size-3.5 animate-spin" />}
          Δοκιμή κύκλου τώρα
        </Button>
        {tick && <p className="mt-2 text-xs">{tick}</p>}
      </div>
    </section>
  );
}
