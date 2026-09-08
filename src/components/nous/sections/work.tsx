import { useState } from "react";
import { Plus, Play, Check, Pause, Minus } from "lucide-react";
import { actions, useNous } from "@/lib/store";
import {
  Badge,
  Card,
  EmptyState,
  GhostButton,
  IconTrash,
  PrimaryButton,
  ProgressBar,
  SectionHeader,
  TextArea,
  TextInput,
  timeAgo,
} from "@/components/nous/ui";

// ── Goals ───────────────────────────────────────────────────────────────────

export function GoalsSection() {
  const { goals } = useNous();
  const [title, setTitle] = useState("");
  const [detail, setDetail] = useState("");

  const create = () => {
    actions.addGoal(title, detail);
    setTitle("");
    setDetail("");
  };

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Goals" subtitle="Στρατηγικοί στόχοι που καθοδηγούν τις αποστολές του agent." />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-3">
          {goals.length === 0 && <EmptyState text="Δεν υπάρχουν στόχοι ακόμη." />}
          {goals.map((g) => (
            <Card key={g.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-display text-base font-semibold">{g.title}</h3>
                    <Badge tone={g.status === "done" ? "ok" : g.status === "paused" ? "warn" : "primary"}>
                      {g.status}
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{g.detail}</p>
                </div>
                <IconTrash onClick={() => actions.removeGoal(g.id)} />
              </div>
              <div className="mt-3 flex items-center gap-3">
                <ProgressBar value={g.progress} tone={g.status === "done" ? "ok" : "primary"} />
                <span className="w-10 text-right font-mono text-xs text-muted-foreground">{g.progress}%</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <GhostButton onClick={() => actions.setGoalProgress(g.id, Math.max(0, g.progress - 10))}>
                  <Minus className="size-3" /> 10%
                </GhostButton>
                <GhostButton onClick={() => actions.setGoalProgress(g.id, Math.min(100, g.progress + 10))}>
                  <Plus className="size-3" /> 10%
                </GhostButton>
                <GhostButton onClick={() => actions.setGoalProgress(g.id, 100)}>
                  <Check className="size-3" /> Ολοκλήρωση
                </GhostButton>
              </div>
            </Card>
          ))}
        </div>

        <Card title="Νέος στόχος" className="h-fit">
          <div className="space-y-3">
            <TextInput value={title} onChange={setTitle} placeholder="Τίτλος στόχου" onEnter={create} />
            <TextArea value={detail} onChange={setDetail} placeholder="Περιγραφή / γιατί" rows={4} />
            <PrimaryButton onClick={create} disabled={!title.trim()} className="w-full">
              <Plus className="size-3.5" /> Προσθήκη στόχου
            </PrimaryButton>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Missions ─────────────────────────────────────────────────────────────────

const missionTone = { queued: "warn", running: "primary", done: "ok", failed: "err" } as const;

export function MissionsSection() {
  const { missions } = useNous();
  const [title, setTitle] = useState("");

  return (
    <div className="p-4 md:p-6">
      <SectionHeader
        title="Missions"
        subtitle="Αποστολές που εκτελεί ο agent στο background — δημιούργησε, τρέξε και παρακολούθησε."
        actions={
          <div className="flex gap-2">
            <TextInput value={title} onChange={setTitle} placeholder="Νέο mission…" onEnter={() => { actions.addMission(title); setTitle(""); }} className="w-52" />
            <PrimaryButton onClick={() => { actions.addMission(title); setTitle(""); }} disabled={!title.trim()}>
              <Plus className="size-3.5" /> Νέο
            </PrimaryButton>
          </div>
        }
      />
      <div className="space-y-3">
        {missions.length === 0 && <EmptyState text="Δεν υπάρχουν missions." />}
        {missions.map((m) => (
          <Card key={m.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-display text-base font-semibold">{m.title}</h3>
                  <Badge tone={missionTone[m.status]}>{m.status}</Badge>
                </div>
                <p className="mt-1 font-mono text-[11px] text-muted-foreground/70">{timeAgo(m.createdAt)}</p>
              </div>
              <IconTrash onClick={() => actions.removeMission(m.id)} />
            </div>

            <div className="mt-3 flex items-center gap-3">
              <ProgressBar value={m.progress} tone={m.status === "failed" ? "warn" : m.status === "done" ? "ok" : "primary"} />
              <span className="w-10 text-right font-mono text-xs text-muted-foreground">{m.progress}%</span>
            </div>

            <div className="mt-3 rounded-lg border border-border bg-background p-3">
              <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground/60">journal</p>
              <ul className="space-y-0.5 font-mono text-xs text-muted-foreground">
                {m.log.slice(-4).map((l, i) => (
                  <li key={i}>› {l}</li>
                ))}
              </ul>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <GhostButton active={m.status === "running"} onClick={() => actions.setMissionStatus(m.id, "running")}>
                <Play className="size-3" /> Εκτέλεση
              </GhostButton>
              <GhostButton onClick={() => actions.setMissionStatus(m.id, "queued")}>
                <Pause className="size-3" /> Σε ουρά
              </GhostButton>
              <GhostButton onClick={() => actions.setMissionStatus(m.id, "done")}>
                <Check className="size-3" /> Ολοκλήρωση
              </GhostButton>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ── Planner ──────────────────────────────────────────────────────────────────

const prio = { low: "muted", med: "warn", high: "err" } as const;

export function PlannerSection() {
  const { planner } = useNous();
  const [title, setTitle] = useState("");
  const [when, setWhen] = useState("");
  const [priority, setPriority] = useState<"low" | "med" | "high">("med");

  const add = () => {
    actions.addPlannerItem(title, when, priority);
    setTitle("");
    setWhen("");
  };

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Planner" subtitle="Ημερήσιος προγραμματισμός εργασιών του agent και δικών σου." />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Card title={`Λίστα (${planner.filter((p) => !p.done).length} ανοιχτά)`}>
          <div className="space-y-2">
            {planner.length === 0 && <EmptyState text="Άδειο πρόγραμμα." />}
            {planner.map((p) => (
              <div
                key={p.id}
                className="flex items-center gap-3 rounded-lg border border-border bg-background px-3 py-2"
              >
                <button
                  onClick={() => actions.togglePlanner(p.id)}
                  className={`flex size-5 shrink-0 items-center justify-center rounded border ${
                    p.done ? "border-ok bg-ok/20 text-ok" : "border-border text-transparent hover:border-primary"
                  }`}
                  aria-label="toggle"
                >
                  <Check className="size-3" />
                </button>
                <div className="min-w-0 flex-1">
                  <p className={`text-sm ${p.done ? "text-muted-foreground line-through" : ""}`}>{p.title}</p>
                  <p className="font-mono text-[11px] text-muted-foreground/70">{p.when}</p>
                </div>
                <Badge tone={prio[p.priority]}>{p.priority}</Badge>
                <IconTrash onClick={() => actions.removePlanner(p.id)} />
              </div>
            ))}
          </div>
        </Card>

        <Card title="Νέα εργασία" className="h-fit">
          <div className="space-y-3">
            <TextInput value={title} onChange={setTitle} placeholder="Τι πρέπει να γίνει;" onEnter={add} />
            <TextInput value={when} onChange={setWhen} placeholder="Πότε; (π.χ. Σήμερα 15:00)" onEnter={add} />
            <div className="flex gap-2">
              {(["low", "med", "high"] as const).map((p) => (
                <GhostButton key={p} active={priority === p} onClick={() => setPriority(p)} className="flex-1">
                  {p}
                </GhostButton>
              ))}
            </div>
            <PrimaryButton onClick={add} disabled={!title.trim()} className="w-full">
              <Plus className="size-3.5" /> Προσθήκη
            </PrimaryButton>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Brain & Memory ────────────────────────────────────────────────────────────

const kindTone = { fact: "primary", decision: "violet", conversation: "muted" } as const;

export function BrainSection() {
  const { memory } = useNous();
  const [text, setText] = useState("");
  const [kind, setKind] = useState<"fact" | "decision" | "conversation">("fact");
  const [filter, setFilter] = useState<"all" | "fact" | "decision" | "conversation">("all");

  const add = () => {
    actions.addMemory(kind, text);
    setText("");
  };
  const shown = memory.filter((m) => filter === "all" || m.kind === filter);

  return (
    <div className="p-4 md:p-6">
      <SectionHeader
        title="Brain & Memory"
        subtitle="Επίμονη μνήμη: γεγονότα, αποφάσεις και συνομιλίες που ο agent θυμάται."
      />
      <Card
        title="Νέα εγγραφή μνήμης"
        className="mb-4"
        actions={
          <div className="flex gap-2">
            {(["fact", "decision", "conversation"] as const).map((k) => (
              <GhostButton key={k} active={kind === k} onClick={() => setKind(k)}>
                {k}
              </GhostButton>
            ))}
          </div>
        }
      >
        <div className="flex gap-2">
          <TextInput value={text} onChange={setText} placeholder="Τι να θυμάται ο ΝΟΥΣ;" onEnter={add} />
          <PrimaryButton onClick={add} disabled={!text.trim()}>
            <Plus className="size-3.5" /> Αποθήκευση
          </PrimaryButton>
        </div>
      </Card>

      <div className="mb-3 flex flex-wrap gap-2">
        {(["all", "fact", "decision", "conversation"] as const).map((f) => (
          <GhostButton key={f} active={filter === f} onClick={() => setFilter(f)}>
            {f} {f !== "all" && `(${memory.filter((m) => m.kind === f).length})`}
          </GhostButton>
        ))}
      </div>

      <div className="space-y-2">
        {shown.length === 0 && <EmptyState text="Καμία εγγραφή." />}
        {shown.map((m) => (
          <div key={m.id} className="flex items-start gap-3 rounded-lg border border-border bg-card px-4 py-3">
            <Badge tone={kindTone[m.kind]}>{m.kind}</Badge>
            <p className="min-w-0 flex-1 text-sm">{m.text}</p>
            <span className="font-mono text-[10px] text-muted-foreground/60">{timeAgo(m.createdAt)}</span>
            <IconTrash onClick={() => actions.removeMemory(m.id)} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── App Builder ────────────────────────────────────────────────────────────────

const appTone = { draft: "muted", building: "warn", live: "ok" } as const;

export function AppBuilderSection() {
  const { apps } = useNous();
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  const create = () => {
    actions.addApp(name, desc);
    setName("");
    setDesc("");
  };

  return (
    <div className="p-4 md:p-6">
      <SectionHeader
        title="App Builder"
        subtitle="Ο agent γράφει, τρέχει και βελτιώνει μικρές εφαρμογές — η app factory."
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="grid gap-3 sm:grid-cols-2">
          {apps.length === 0 && <EmptyState text="Δεν έχει φτιαχτεί καμία εφαρμογή." />}
          {apps.map((a) => (
            <Card key={a.id}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="font-mono text-sm font-semibold text-primary">{a.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{a.description}</p>
                </div>
                <IconTrash onClick={() => actions.removeApp(a.id)} />
              </div>
              <div className="mt-3 flex items-center justify-between">
                <Badge tone={appTone[a.status]}>{a.status}</Badge>
                <div className="flex gap-2">
                  {a.status !== "building" && (
                    <GhostButton onClick={() => actions.setAppStatus(a.id, "building")}>
                      <Play className="size-3" /> Build
                    </GhostButton>
                  )}
                  {a.status !== "live" && (
                    <GhostButton onClick={() => actions.setAppStatus(a.id, "live")}>
                      <Check className="size-3" /> Deploy
                    </GhostButton>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>

        <Card title="Νέα εφαρμογή" className="h-fit">
          <div className="space-y-3">
            <TextInput value={name} onChange={setName} placeholder="όνομα-εφαρμογής" onEnter={create} />
            <TextArea value={desc} onChange={setDesc} placeholder="Τι κάνει;" rows={4} />
            <PrimaryButton onClick={create} disabled={!name.trim()} className="w-full">
              <Plus className="size-3.5" /> Δημιουργία
            </PrimaryButton>
          </div>
        </Card>
      </div>
    </div>
  );
}
