import { useState } from "react";
import { Check, Copy, Loader2, Play, Search, X } from "lucide-react";
import {
  canRunNextStep,
  filterMissions,
  missionStatusMeta,
  missionToneClass,
  summarizeMissions,
  type LiveMission,
  type MissionFilterTab,
  type RunNextOutcome,
} from "./mission-status";

export type { LiveMission } from "./mission-status";

export function MissionList({
  missions,
  onRunNext,
}: {
  missions: LiveMission[];
  /** Runs the next step of a mission (POST /remote/missions/run-next). */
  onRunNext?: (id: string) => Promise<RunNextOutcome>;
}) {
  const [tab, setTab] = useState<MissionFilterTab>("all");
  const [query, setQuery] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  // One step at a time: the backend runs missions sequentially anyway.
  const [runningId, setRunningId] = useState<string | null>(null);
  const [outcomes, setOutcomes] = useState<Record<string, RunNextOutcome>>({});

  if (missions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Δεν υπάρχουν ενεργά missions στο live stream.</p>
    );
  }

  const summary = summarizeMissions(missions);
  const filtered = filterMissions(missions, tab, query);

  const copyId = async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // ignore
    }
  };

  const runNext = async (id: string) => {
    if (!onRunNext || runningId) return;
    setRunningId(id);
    const outcome = await onRunNext(id);
    setOutcomes((prev) => ({ ...prev, [id]: outcome }));
    setRunningId(null);
  };

  const tabs: Array<{ id: MissionFilterTab; label: string; count: number }> = [
    { id: "all", label: "Όλες", count: missions.length },
    { id: "active", label: "Ενεργές", count: summary.active },
    { id: "awaiting", label: "Θέλουν προσοχή", count: summary.awaiting },
    { id: "failed", label: "Αποτυχίες", count: summary.failed },
    { id: "completed", label: "Ολοκληρωμένες", count: summary.completed },
  ];

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                tab === item.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted/40 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {item.label}
              <span className="ml-1 opacity-70">({item.count})</span>
            </button>
          ))}
        </div>

        {missions.length > 2 && (
          <div className="relative min-w-40 sm:max-w-48">
            <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Αναζήτηση…"
              className="w-full rounded-md border border-border bg-background py-1.5 pl-8 pr-7 text-xs outline-none focus:border-violet"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
                title="Καθαρισμός αναζήτησης"
              >
                <X className="size-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
          {query
            ? `Δεν βρέθηκαν αποστολές για «${query}».`
            : "Δεν υπάρχουν αποστολές σε αυτή την κατάσταση."}
        </div>
      ) : (
        <ul className="divide-y divide-border/60">
          {filtered.map((mission) => {
            const meta = missionStatusMeta(mission.status);
            const total = mission.tasksTotal ?? 0;
            const done = mission.tasksDone ?? 0;
            const pct = total ? Math.round((done / total) * 100) : 0;
            const step = mission.currentStepStatus
              ? missionStatusMeta(mission.currentStepStatus)
              : null;
            const outcome = outcomes[mission.id];
            return (
              <li key={mission.id} className="group py-2.5">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-foreground">
                        {mission.title}
                      </span>
                      <button
                        type="button"
                        onClick={() => void copyId(mission.id)}
                        className="opacity-0 transition-opacity group-hover:opacity-100 text-muted-foreground hover:text-foreground"
                        title={`Αντιγραφή ID: ${mission.id}`}
                      >
                        {copiedId === mission.id ? (
                          <Check className="size-3 text-ok" />
                        ) : (
                          <Copy className="size-3" />
                        )}
                      </button>
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      ID: {mission.id}
                    </span>
                  </div>

                  <span
                    className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
                      missionToneClass[meta.tone]
                    }`}
                  >
                    {meta.active && meta.tone === "active" ? (
                      <span className="mr-1 size-1.5 rounded-full bg-primary animate-pulse" />
                    ) : null}
                    {meta.label}
                  </span>
                </div>
                {total > 0 && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div
                      className="h-1 flex-1 overflow-hidden rounded-full bg-muted/50"
                      role="progressbar"
                      aria-valuenow={pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`Πρόοδος ${mission.title}`}
                    >
                      <div
                        className={`h-full rounded-full transition-[width] duration-500 ${
                          meta.tone === "danger"
                            ? "bg-destructive"
                            : meta.tone === "ok"
                              ? "bg-ok"
                              : "bg-primary"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                      {done}/{total}
                    </span>
                  </div>
                )}
                {mission.currentStep && (meta.active || meta.tone === "warn") && (
                  <p className="mt-1 truncate text-[11px] text-muted-foreground">
                    Βήμα: {mission.currentStep}
                    {step && mission.currentStepStatus !== "pending" ? ` · ${step.label}` : ""}
                  </p>
                )}
                {onRunNext && (canRunNextStep(mission) || runningId === mission.id) && (
                  <button
                    type="button"
                    onClick={() => void runNext(mission.id)}
                    disabled={runningId !== null}
                    className="mt-2 inline-flex items-center gap-1 rounded-md border border-primary/30 px-2 py-1 text-[11px] text-primary hover:bg-primary/10 disabled:opacity-50"
                  >
                    {runningId === mission.id ? (
                      <Loader2 className="size-3 animate-spin" />
                    ) : (
                      <Play className="size-3" />
                    )}
                    {runningId === mission.id ? "Εκτελείται…" : "Επόμενο βήμα"}
                  </button>
                )}
                {outcome && runningId !== mission.id && (
                  <p
                    role="status"
                    className={`mt-1.5 text-[11px] ${outcome.ok ? "text-ok" : "text-warn"}`}
                  >
                    {outcome.message}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
