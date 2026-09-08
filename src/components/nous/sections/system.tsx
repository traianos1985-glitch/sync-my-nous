import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Play, Power, Terminal as TerminalIcon } from "lucide-react";
import { actions, useNous } from "@/lib/store";
import {
  Badge,
  Card,
  EmptyState,
  GhostButton,
  PrimaryButton,
  SectionHeader,
  Stat,
  timeAgo,
} from "@/components/nous/ui";

const levelTone = { ok: "text-ok", info: "text-primary", warn: "text-warn", err: "text-destructive" } as const;

// ── Approvals / Pending ────────────────────────────────────────────────────

export function ApprovalsSection() {
  const { approvals } = useNous();
  const pending = approvals.filter((a) => a.status === "pending");
  const resolved = approvals.filter((a) => a.status !== "pending");

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Approvals" subtitle="Αυτόνομες προτάσεις του agent — εγκρίνεις ή απορρίπτεις." />
      <Card title={`Εκκρεμείς (${pending.length})`} className="mb-4">
        {pending.length === 0 ? (
          <EmptyState text="Καμία εκκρεμής πρόταση." />
        ) : (
          <div className="space-y-3">
            {pending.map((a) => (
              <div key={a.id} className="rounded-xl border border-border bg-background p-4">
                <p className="text-sm font-medium">{a.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{a.why}</p>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => actions.resolveApproval(a.id, "approved")}
                    className="rounded-md bg-ok/20 px-3 py-1.5 text-xs font-semibold text-ok hover:bg-ok/30"
                  >
                    Έγκριση → δημιουργία mission
                  </button>
                  <button
                    onClick={() => actions.resolveApproval(a.id, "rejected")}
                    className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent"
                  >
                    Απόρριψη
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {resolved.length > 0 && (
        <Card title="Ιστορικό">
          <div className="space-y-2">
            {resolved.map((a) => (
              <div key={a.id} className="flex items-center justify-between border-b border-border/50 py-2 text-sm last:border-0">
                <span className="truncate text-muted-foreground">{a.title}</span>
                <Badge tone={a.status === "approved" ? "ok" : "err"}>{a.status}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

export function PendingSection() {
  const { missions, approvals } = useNous();
  const queued = missions.filter((m) => m.status === "queued");
  const pending = approvals.filter((a) => a.status === "pending");

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Pending" subtitle="Όλα όσα περιμένουν ενέργεια ή εκτέλεση." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title={`Missions σε ουρά (${queued.length})`}>
          {queued.length === 0 ? (
            <EmptyState text="Κανένα mission σε αναμονή." />
          ) : (
            <div className="space-y-2">
              {queued.map((m) => (
                <div key={m.id} className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <span className="truncate">{m.title}</span>
                  <GhostButton onClick={() => actions.setMissionStatus(m.id, "running")}>
                    <Play className="size-3" /> Εκτέλεση
                  </GhostButton>
                </div>
              ))}
            </div>
          )}
        </Card>
        <Card title={`Εκκρεμείς εγκρίσεις (${pending.length})`}>
          {pending.length === 0 ? (
            <EmptyState text="Καμία εκκρεμότητα." />
          ) : (
            <div className="space-y-2">
              {pending.map((a) => (
                <div key={a.id} className="rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  {a.title}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

// ── Command console ───────────────────────────────────────────────────────────

const HELP = `Διαθέσιμες εντολές:
  help                     — αυτή η βοήθεια
  status                   — κατάσταση συστήματος
  mission <τίτλος>         — δημιουργία mission
  goal <τίτλος>            — δημιουργία στόχου
  remember <κείμενο>       — αποθήκευση στη μνήμη
  backup                   — χειροκίνητο backup
  clear                    — καθάρισμα κονσόλας`;

export function CommandSection() {
  const state = useNous();
  const [input, setInput] = useState("");
  const [lines, setLines] = useState<string[]>(["NOUS shell — γράψε «help» για εντολές."]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const run = () => {
    const cmd = input.trim();
    if (!cmd) return;
    const out: string[] = [`$ ${cmd}`];
    const [verb, ...rest] = cmd.split(" ");
    const arg = rest.join(" ");

    switch (verb) {
      case "help":
        out.push(HELP);
        break;
      case "status":
        out.push(
          `missions: ${state.missions.length} (running ${state.missions.filter((m) => m.status === "running").length})`,
          `goals: ${state.goals.length} · memory: ${state.memory.length} · docs: ${state.documents.length}`,
          `autonomy: ${state.settings.autonomy ? "on" : "off"} · model: ${state.settings.model}`,
        );
        break;
      case "mission":
        if (arg) { actions.addMission(arg); out.push(`✓ mission «${arg}» δημιουργήθηκε`); }
        else out.push("χρήση: mission <τίτλος>");
        break;
      case "goal":
        if (arg) { actions.addGoal(arg, "Δημιουργήθηκε από κονσόλα"); out.push(`✓ goal «${arg}» δημιουργήθηκε`); }
        else out.push("χρήση: goal <τίτλος>");
        break;
      case "remember":
        if (arg) { actions.addMemory("fact", arg); out.push("✓ αποθηκεύτηκε στη μνήμη"); }
        else out.push("χρήση: remember <κείμενο>");
        break;
      case "backup":
        actions.runBackup();
        out.push("✓ backup ολοκληρώθηκε");
        break;
      case "clear":
        setLines([]);
        setInput("");
        return;
      default:
        out.push(`άγνωστη εντολή: ${verb} — γράψε «help»`);
    }
    setLines((l) => [...l, ...out]);
    setInput("");
  };

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Command" subtitle="Ζωντανή κονσόλα εντολών προς τον agent." />
      <div className="rounded-2xl border border-border bg-background">
        <div className="flex items-center gap-2 border-b border-border px-4 py-2">
          <TerminalIcon className="size-4 text-primary" />
          <span className="font-mono text-xs text-muted-foreground">nous@os:~</span>
        </div>
        <div className="h-[52vh] overflow-y-auto p-4 font-mono text-xs leading-relaxed">
          {lines.map((l, i) => (
            <pre key={i} className={`whitespace-pre-wrap ${l.startsWith("$") ? "text-primary" : "text-muted-foreground"}`}>
              {l}
            </pre>
          ))}
          <div ref={endRef} />
        </div>
        <div className="flex items-center gap-2 border-t border-border px-4 py-2">
          <span className="font-mono text-xs text-primary">$</span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.nativeEvent.isComposing && e.keyCode !== 229) run();
            }}
            placeholder="γράψε εντολή…"
            className="flex-1 bg-transparent font-mono text-xs text-foreground outline-none placeholder:text-muted-foreground/50"
          />
        </div>
      </div>
    </div>
  );
}

// ── System monitor ──────────────────────────────────────────────────────────

export function SystemMonitorSection() {
  const { activity, missions, settings } = useNous();
  const [series, setSeries] = useState(() =>
    Array.from({ length: 20 }, (_, i) => ({ t: i, cpu: 30 + Math.random() * 20, ram: 55 + Math.random() * 15 })),
  );

  useEffect(() => {
    const load = missions.filter((m) => m.status === "running").length;
    const id = setInterval(() => {
      setSeries((s) => {
        const last = s[s.length - 1];
        const cpu = Math.max(8, Math.min(96, last.cpu + (Math.random() - 0.5) * 18 + load * 4));
        const ram = Math.max(20, Math.min(94, last.ram + (Math.random() - 0.5) * 10));
        return [...s.slice(1), { t: last.t + 1, cpu, ram }];
      });
    }, 1500);
    return () => clearInterval(id);
  }, [missions]);

  const cur = series[series.length - 1];

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="System" subtitle="Ζωντανά μετρικά πόρων και υγείας του service." />
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="CPU" value={`${cur.cpu.toFixed(0)}%`} tone={cur.cpu > 85 ? "warn" : "ok"} />
        <Stat label="RAM" value={`${cur.ram.toFixed(0)}%`} tone={cur.ram > 85 ? "warn" : undefined} />
        <Stat label="Health" value="online" tone="ok" />
        <Stat label="Model" value={(settings.model.split("/")[1] ?? settings.model).slice(0, 12)} />
      </div>

      <Card title="Χρήση πόρων (ζωντανά)">
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={series} margin={{ top: 6, right: 6, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gcpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.5} />
                <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gram" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-violet)" stopOpacity={0.5} />
                <stop offset="100%" stopColor="var(--color-violet)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="t" tick={false} axisLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: "var(--color-muted-foreground)", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: "var(--color-card)",
                border: "1px solid var(--color-border)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Area type="monotone" dataKey="cpu" stroke="var(--color-primary)" fill="url(#gcpu)" strokeWidth={2} name="CPU %" />
            <Area type="monotone" dataKey="ram" stroke="var(--color-violet)" fill="url(#gram)" strokeWidth={2} name="RAM %" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Log συστήματος" className="mt-4">
        <div className="max-h-64 space-y-1.5 overflow-y-auto">
          {activity.map((a) => (
            <div key={a.id} className="flex items-baseline gap-2 font-mono text-xs">
              <span className={`uppercase ${levelTone[a.level]}`}>{a.level}</span>
              <span className="flex-1 text-muted-foreground">{a.text}</span>
              <span className="text-muted-foreground/50">{timeAgo(a.at)}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ── Graphs ────────────────────────────────────────────────────────────────────

export function GraphsSection() {
  const { missions, goals } = useNous();

  const missionData = useMemo(() => {
    const by: Record<string, number> = { queued: 0, running: 0, done: 0, failed: 0 };
    for (const m of missions) by[m.status]++;
    return Object.entries(by).map(([name, value]) => ({ name, value }));
  }, [missions]);

  const colors = ["var(--color-warn)", "var(--color-primary)", "var(--color-ok)", "var(--color-destructive)"];

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Graphs" subtitle="Οπτικοποίηση των δεδομένων του workspace." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Missions ανά κατάσταση">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={missionData} margin={{ top: 6, right: 6, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "var(--color-muted-foreground)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: "var(--color-muted-foreground)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: "var(--color-accent)" }}
                contentStyle={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {missionData.map((_, i) => (
                  <Cell key={i} fill={colors[i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Πρόοδος στόχων">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              layout="vertical"
              data={goals.map((g) => ({ name: g.title.slice(0, 18), value: g.progress }))}
              margin={{ top: 6, right: 12, left: 40, bottom: 0 }}
            >
              <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: "var(--color-muted-foreground)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: "var(--color-muted-foreground)", fontSize: 10 }} width={90} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: "var(--color-accent)" }}
                contentStyle={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="value" fill="var(--color-violet)" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}

// ── Analyst ────────────────────────────────────────────────────────────────────

export function AnalystSection() {
  const { missions, goals, memory, documents, activity } = useNous();
  const done = missions.filter((m) => m.status === "done").length;
  const rate = missions.length ? Math.round((done / missions.length) * 100) : 0;
  const avgGoal = goals.length ? Math.round(goals.reduce((a, g) => a + g.progress, 0) / goals.length) : 0;
  const errs = activity.filter((a) => a.level === "err").length;

  const insights = [
    `Ποσοστό ολοκλήρωσης missions: ${rate}%.`,
    `Μέση πρόοδος στόχων: ${avgGoal}%.`,
    `Η μνήμη περιέχει ${memory.length} εγγραφές και ${documents.length} έγγραφα.`,
    errs > 0 ? `Εντοπίστηκαν ${errs} σφάλματα στο πρόσφατο log.` : "Κανένα σφάλμα στο πρόσφατο log.",
  ];

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Analyst" subtitle="Υπολογισμένες μετρήσεις και συμπεράσματα από τα δεδομένα σου." />
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Ολοκλήρωση missions" value={`${rate}%`} tone={rate > 50 ? "ok" : "warn"} />
        <Stat label="Μ.Ο. στόχων" value={`${avgGoal}%`} />
        <Stat label="Μνήμη" value={memory.length} />
        <Stat label="Σφάλματα" value={errs} tone={errs ? "err" : "ok"} />
      </div>
      <Card title="Συμπεράσματα">
        <ul className="space-y-2">
          {insights.map((t, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
              <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
              {t}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

// ── Generic module panel ────────────────────────────────────────────────────

export function ModuleSection({
  id,
  label,
  description,
  tips,
}: {
  id: string;
  label: string;
  description: string;
  tips: string[];
}) {
  const state = useNous();
  const mod = state.modules[id] ?? { enabled: false, runs: 0, lastRun: null };
  const log = state.activity.filter((a) => a.text.startsWith(label));

  return (
    <div className="p-4 md:p-6">
      <SectionHeader
        title={label}
        subtitle={description}
        actions={
          <div className="flex gap-2">
            <PrimaryButton onClick={() => actions.runModule(id, label)}>
              <Play className="size-3.5" /> Εκτέλεση
            </PrimaryButton>
            <GhostButton active={mod.enabled} onClick={() => actions.toggleModule(id)}>
              <Power className="size-3.5" /> {mod.enabled ? "Ενεργό" : "Ανενεργό"}
            </GhostButton>
          </div>
        }
      />
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-3">
        <Stat label="Κατάσταση" value={mod.enabled ? "ενεργό" : "ανενεργό"} tone={mod.enabled ? "ok" : "warn"} />
        <Stat label="Εκτελέσεις" value={mod.runs} />
        <Stat label="Τελευταία" value={timeAgo(mod.lastRun)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Τι κάνει αυτό το module">
          <ul className="space-y-2">
            {tips.map((t, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                {t}
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Δραστηριότητα module">
          {log.length === 0 ? (
            <EmptyState text="Καμία εκτέλεση ακόμη. Πάτησε «Εκτέλεση»." />
          ) : (
            <div className="space-y-1.5">
              {log.map((a) => (
                <div key={a.id} className="flex justify-between font-mono text-xs text-muted-foreground">
                  <span>{a.text}</span>
                  <span className="text-muted-foreground/50">{timeAgo(a.at)}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
