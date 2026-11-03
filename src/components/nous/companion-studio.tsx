import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Circle, Loader2, RefreshCw, Smartphone } from "lucide-react";

import { Button } from "@/components/ui/button";
import { nousFetch } from "@/lib/nous-api";
import {
  canSendCompanionCommand,
  companionSetupSteps,
  validateTap,
  type CompanionStatus,
} from "./companion-model";

type CommandResult = { ok: boolean; command?: string; error?: string };

export function CompanionStudio({ connected }: { connected: boolean }) {
  const [status, setStatus] = useState<CompanionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [last, setLast] = useState<string | null>(null);
  const [x, setX] = useState("");
  const [y, setY] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setStatus(await nousFetch<CompanionStatus>("/remote/companion/status"));
    } catch (err) {
      setStatus(null);
      setLoadError(err instanceof Error ? err.message : "Αποτυχία φόρτωσης");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (connected) queueMicrotask(refresh);
    else setLoading(false);
  }, [connected, refresh]);

  const steps = companionSetupSteps(status);
  const ready = canSendCompanionCommand(status, connected);

  async function send(path: string, label: string, body?: Record<string, unknown>) {
    setBusy(label);
    try {
      const res = await nousFetch<CommandResult>(path, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      });
      setLast(res.ok ? `${label}: στάλθηκε` : `${label}: απέτυχε (${res.error ?? "άγνωστο"})`);
    } catch (err) {
      setLast(`${label}: ${err instanceof Error ? err.message : "απέτυχε"}`);
    } finally {
      setBusy(null);
    }
  }

  const tap = validateTap(x, y);

  return (
    <div className="mx-auto min-w-0 max-w-4xl space-y-4">
      <section className="rounded-2xl border border-border bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-xl bg-signal/15 text-signal">
              <Smartphone className="size-5" />
            </div>
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-signal">
                Android companion
              </p>
              <h2 className="font-display text-xl font-semibold">Έλεγχος κινητού</h2>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void refresh()}
            disabled={loading || !connected}
          >
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
            Ανανέωση
          </Button>
        </div>
        <p
          className={`mt-4 text-sm font-semibold ${ready ? "text-ok" : "text-warn"}`}
          role="status"
        >
          {!connected
            ? "Βάλε το NOUS token στις Ρυθμίσεις."
            : ready
              ? "Η σύνδεση με το κινητό είναι έτοιμη."
              : "Η σύνδεση με το κινητό δεν είναι ακόμη διαθέσιμη."}
        </p>
        {loadError && <p className="mt-1 text-xs text-destructive">{loadError}</p>}
        <ol className="mt-4 space-y-3">
          {steps.map((step) => (
            <li
              key={step.id}
              className="flex gap-3 rounded-xl border border-border/70 bg-background/40 p-3"
            >
              {step.done ? (
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-ok" />
              ) : (
                <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium">{step.label}</p>
                <p className="mt-0.5 break-words text-xs text-muted-foreground">{step.hint}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-2xl border border-border bg-card p-5">
        <h3 className="font-display text-base font-semibold">Εντολές</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            { path: "/remote/companion/home", label: "Αρχική" },
            { path: "/remote/companion/back", label: "Πίσω" },
            { path: "/remote/companion/ui-tree", label: "Δέντρο οθόνης" },
          ].map((cmd) => (
            <Button
              key={cmd.path}
              variant="outline"
              size="sm"
              disabled={!ready || busy !== null}
              onClick={() => void send(cmd.path, cmd.label)}
            >
              {busy === cmd.label && <Loader2 className="size-3.5 animate-spin" />}
              {cmd.label}
            </Button>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap items-end gap-2">
          <label className="text-xs">
            X
            <input
              value={x}
              onChange={(e) => setX(e.target.value)}
              inputMode="numeric"
              className="mt-1 block w-24 rounded-lg border border-input bg-background p-2 text-sm"
            />
          </label>
          <label className="text-xs">
            Y
            <input
              value={y}
              onChange={(e) => setY(e.target.value)}
              inputMode="numeric"
              className="mt-1 block w-24 rounded-lg border border-input bg-background p-2 text-sm"
            />
          </label>
          <Button
            size="sm"
            disabled={!ready || !tap || busy !== null}
            onClick={() => tap && void send("/remote/companion/tap", "Πάτημα", tap)}
          >
            Πάτημα
          </Button>
        </div>
        {!ready && (
          <p className="mt-3 text-xs text-muted-foreground">
            Οι εντολές ενεργοποιούνται όταν ολοκληρωθούν τα βήματα παραπάνω.
          </p>
        )}
        {last && <p className="mt-3 text-xs">{last}</p>}
      </section>
    </div>
  );
}
