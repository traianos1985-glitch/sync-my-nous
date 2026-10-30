import { useCallback, useEffect, useState } from "react";
import { Brain, CalendarDays, CheckCircle2, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { nousFetch } from "@/lib/nous-api";

type Briefing = {
  summary?: string;
  memory?: { episodic: unknown[]; semantic: unknown[]; procedural: unknown[] };
  goals?: unknown[];
  projects?: unknown[];
  active_learning_topics?: string[];
};

const layers = [
  ["episodic", "Επεισοδιακή", "Τι κάναμε πρόσφατα", "text-violet"],
  ["semantic", "Σημασιολογική", "Projects και προτιμήσεις", "text-signal"],
  ["procedural", "Διαδικαστική", "Τι έμαθε να κάνει ο NOUS", "text-ok"],
] as const;

export function CognitiveMemoryPanel() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);

  const loadBriefing = useCallback(async () => {
    setLoading(true);
    try {
      setBriefing(await nousFetch<Briefing>("/remote/daily-brief", { timeoutMs: 30_000 }));
    } catch {
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBriefing();
  }, [loadBriefing]);

  return (
    <section
      className="mt-4 overflow-hidden rounded-2xl border border-border bg-card/80"
      aria-labelledby="cognitive-memory-title"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 p-4">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Brain className="size-5" />
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
              Unified cognitive memory
            </p>
            <h2 id="cognitive-memory-title" className="text-base font-semibold">
              Executive Daily Briefing
            </h2>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void loadBriefing()}
          disabled={loading}
          aria-label="Refresh daily briefing"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
        </Button>
      </div>
      <div className="grid gap-2 p-4 md:grid-cols-3">
        {layers.map(([key, title, description, color]) => {
          const entries = briefing?.memory?.[key as keyof NonNullable<Briefing["memory"]>] ?? [];
          return (
            <div key={key} className="rounded-xl border border-border/70 bg-background/40 p-3">
              <div className="flex items-center gap-2">
                <Sparkles className={`size-4 ${color}`} />
                <span className="text-sm font-semibold">{title}</span>
                <span className="ml-auto rounded-full bg-muted px-2 py-0.5 font-mono text-[10px]">
                  {entries.length}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
              <p className="mt-3 line-clamp-2 text-xs text-foreground/80">
                {entries.length
                  ? String(entries[0])
                  : "Δεν υπάρχουν καταγεγραμμένες εγγραφές ακόμη."}
              </p>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-3 border-t border-border/70 bg-background/20 px-4 py-3 text-xs">
        <CalendarDays className="size-4 text-primary" />
        <span className="font-medium">{briefing?.summary ?? "Ημερήσια εικόνα ΝΟΥΣ"}</span>
        <span className="text-muted-foreground">
          {briefing?.goals?.length ?? 0} στόχοι · {briefing?.projects?.length ?? 0} projects
        </span>
        <span className="ml-auto flex items-center gap-1 text-ok">
          <CheckCircle2 className="size-3.5" />
          Συγχρονισμένο
        </span>
      </div>
    </section>
  );
}
