import { useState } from "react";
import { AlertTriangle, Loader2, Network, Play } from "lucide-react";

import { Button } from "@/components/ui/button";
import { nousFetch } from "@/lib/nous-api";
import {
  buildSwarmView,
  MAX_MISSION_LENGTH,
  validateMission,
  type SwarmNode,
  type SwarmResult,
} from "./swarm-model";

function NodeCard({ node, leader }: { node: SwarmNode; leader?: boolean }) {
  return (
    <div
      className={`min-w-0 rounded-2xl border p-4 ${leader ? "border-primary/50 bg-primary/10" : "border-border bg-background/60"}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
          {leader ? "Leader" : "Worker"}
        </p>
        <span
          className={`rounded-full border px-2 py-0.5 text-[10px] ${node.executed ? "border-ok/40 text-ok" : "border-warn/40 text-warn"}`}
        >
          {node.executed ? "Εκτελέστηκε" : "Προσομοίωση"}
        </span>
      </div>
      <h3 className="mt-2 font-display text-base font-semibold">{node.label}</h3>
      <p className="text-xs text-muted-foreground">{node.description}</p>
      <p className="mt-2 text-xs font-medium">{node.statusLabel}</p>
      {node.task && <p className="mt-2 break-words text-xs text-muted-foreground">{node.task}</p>}
      {node.summary && <p className="mt-2 break-words text-xs">{node.summary}</p>}
    </div>
  );
}

export function SwarmStudio({ connected }: { connected: boolean }) {
  const [mission, setMission] = useState("");
  const [result, setResult] = useState<SwarmResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const view = buildSwarmView(result);

  async function run() {
    const invalid = validateMission(mission);
    if (invalid) {
      setError(invalid);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await nousFetch<{ success: boolean; result?: SwarmResult; error?: string }>(
        "/api/ops/swarm/run",
        { method: "POST", body: JSON.stringify({ mission: mission.trim() }) },
      );
      if (!res.success || !res.result) throw new Error(res.error ?? "Αποτυχία swarm");
      setResult(res.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Αποτυχία swarm");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto min-w-0 max-w-5xl space-y-4">
      <section className="rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Network className="size-5" />
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
              Multi-agent swarm
            </p>
            <h2 className="font-display text-xl font-semibold">Swarm Orchestrator</h2>
          </div>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          Ο Architect σπάει την αποστολή σε εργασίες και τις αναθέτει σε Researcher, Coder και
          Reviewer. Αυτή τη στιγμή το swarm φτιάχνει μόνο σχέδιο: δεν αλλάζει αρχεία και δεν τρέχει
          tests. Για πραγματική δουλειά χρησιμοποίησε Missions με έγκριση.
        </p>
        {!connected && (
          <p role="status" className="mt-3 rounded-xl border border-warn/40 bg-warn/10 p-3 text-xs">
            Βάλε το NOUS token στις Ρυθμίσεις για να τρέξει το swarm.
          </p>
        )}
        <label htmlFor="swarm-mission" className="mt-4 block text-xs font-medium">
          Αποστολή
        </label>
        <textarea
          id="swarm-mission"
          value={mission}
          onChange={(e) => setMission(e.target.value)}
          maxLength={MAX_MISSION_LENGTH}
          rows={3}
          placeholder="π.χ. Πρόσθεσε σελίδα επικοινωνίας στην εφαρμογή μου"
          className="mt-1 w-full resize-none rounded-xl border border-input bg-background p-3 text-sm outline-none focus:border-primary"
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button onClick={() => void run()} disabled={busy || !connected}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            Εκκίνηση swarm
          </Button>
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
      </section>

      {view.leader && (
        <section
          className="rounded-2xl border border-border bg-card p-5"
          aria-label="Δίκτυο πρακτόρων"
        >
          {view.simulated && (
            <div className="mb-4 flex items-start gap-2 rounded-xl border border-warn/40 bg-warn/10 p-3 text-xs">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warn" />
              {result?.notice ?? "Προσομοίωση σχεδίου: δεν εκτελέστηκε πραγματική εργασία."}
            </div>
          )}
          <div className="mx-auto max-w-sm">
            <NodeCard node={view.leader} leader />
          </div>
          <div className="mx-auto h-6 w-px bg-border" aria-hidden />
          <div className="grid gap-3 border-t border-border pt-6 sm:grid-cols-3">
            {view.workers.map((node) => (
              <NodeCard key={`${node.role}-${node.task}`} node={node} />
            ))}
          </div>
          <p className="mt-4 text-[11px] text-muted-foreground">
            {view.executedCount} από {view.workers.length + 1} πράκτορες εκτέλεσαν πραγματική
            εργασία · διάρκεια {result?.duration_s ?? 0}s
          </p>
        </section>
      )}
    </div>
  );
}
