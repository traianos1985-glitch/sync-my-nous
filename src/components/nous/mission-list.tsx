import { useState } from "react";
import { Check, Copy, Search, X } from "lucide-react";
import {
  filterMissions,
  missionStatusMeta,
  missionToneClass,
  summarizeMissions,
  type MissionFilterTab,
} from "./mission-status";

export type LiveMission = { id: string; title: string; status: string };

export function MissionList({ missions }: { missions: LiveMission[] }) {
  const [tab, setTab] = useState<MissionFilterTab>("all");
  const [query, setQuery] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

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

  const tabs: Array<{ id: MissionFilterTab; label: string; count: number }> = [
    { id: "all", label: "Όλες", count: missions.length },
    { id: "active", label: "Ενεργές", count: summary.active },
    { id: "awaiting", label: "Προς έγκριση", count: summary.awaiting },
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
            return (
              <li
                key={mission.id}
                className="group flex flex-col gap-1 py-2.5 sm:flex-row sm:items-center sm:justify-between sm:gap-3"
              >
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
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
