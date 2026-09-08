import { actions, useNous } from "@/lib/store";
import { Badge, Card, ProgressBar, Stat, timeAgo } from "@/components/nous/ui";

const levelTone = { ok: "text-ok", info: "text-primary", warn: "text-warn", err: "text-destructive" } as const;

export function HomeSection({ onNavigate }: { onNavigate: (id: string) => void }) {
  const { goals, missions, documents, memory, activity, approvals } = useNous();
  const running = missions.filter((m) => m.status === "running").length;
  const pending = approvals.filter((a) => a.status === "pending");
  const activeGoals = goals.filter((g) => g.status === "active");

  return (
    <div className="p-4 md:p-6">
      <div className="rounded-2xl border border-border bg-gradient-to-br from-violet/20 to-primary/10 p-5">
        <h1 className="font-display text-2xl font-bold">Καλώς ήρθες στον ΝΟΥΣ</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Agent chat, workspace, αυτονομία και έλεγχος συστήματος — όλα σε μία οθόνη, ζωντανά.
        </p>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Missions ενεργά" value={running} tone={running ? "warn" : undefined} />
        <Stat label="Ενεργοί στόχοι" value={activeGoals.length} />
        <Stat label="Έγγραφα" value={documents.length} />
        <Stat label="Εγγραφές μνήμης" value={memory.length} tone="ok" />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card
          title="Στόχοι σε εξέλιξη"
          actions={
            <button onClick={() => onNavigate("goals")} className="font-mono text-xs text-primary hover:underline">
              όλα →
            </button>
          }
        >
          <div className="space-y-3">
            {activeGoals.slice(0, 3).map((g) => (
              <div key={g.id}>
                <div className="mb-1 flex items-center justify-between gap-2 text-sm">
                  <span className="truncate">{g.title}</span>
                  <span className="font-mono text-xs text-muted-foreground">{g.progress}%</span>
                </div>
                <ProgressBar value={g.progress} />
              </div>
            ))}
            {activeGoals.length === 0 && <p className="text-sm text-muted-foreground">Κανένας ενεργός στόχος.</p>}
          </div>
        </Card>

        <Card
          title="Missions"
          actions={
            <button onClick={() => onNavigate("missions")} className="font-mono text-xs text-primary hover:underline">
              όλα →
            </button>
          }
        >
          <div className="space-y-2">
            {missions.slice(0, 4).map((m) => (
              <div key={m.id} className="flex items-center justify-between gap-3 border-b border-border/50 py-1.5 text-sm last:border-0">
                <span className="truncate">{m.title}</span>
                <Badge
                  tone={
                    m.status === "running" ? "primary" : m.status === "done" ? "ok" : m.status === "failed" ? "err" : "warn"
                  }
                >
                  {m.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card
          title="Προτάσεις του ΝΟΥ"
          actions={
            <button onClick={() => onNavigate("approvals")} className="font-mono text-xs text-primary hover:underline">
              approvals →
            </button>
          }
        >
          {pending.length === 0 ? (
            <p className="text-sm text-muted-foreground">Καμία εκκρεμής πρόταση.</p>
          ) : (
            <div className="space-y-3">
              {pending.map((i) => (
                <div key={i.id} className="rounded-xl border border-border bg-background p-3">
                  <p className="text-sm font-medium">{i.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{i.why}</p>
                  <div className="mt-2 flex gap-2">
                    <button
                      onClick={() => actions.resolveApproval(i.id, "approved")}
                      className="rounded-md bg-ok/20 px-3 py-1 text-xs font-semibold text-ok hover:bg-ok/30"
                    >
                      Έγκριση
                    </button>
                    <button
                      onClick={() => actions.resolveApproval(i.id, "rejected")}
                      className="rounded-md border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-accent"
                    >
                      Απόρριψη
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Πρόσφατη δραστηριότητα">
          <div className="space-y-1.5">
            {activity.slice(0, 6).map((a) => (
              <div key={a.id} className="flex items-baseline gap-2 text-sm">
                <span className={`font-mono text-[10px] uppercase ${levelTone[a.level]}`}>{a.level}</span>
                <span className="flex-1 truncate text-muted-foreground">{a.text}</span>
                <span className="font-mono text-[10px] text-muted-foreground/60">{timeAgo(a.at)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
