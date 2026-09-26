import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  Loader2,
  Menu,
  RotateCcw,
  ScanLine,
  Send,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { navGroups, navLabel } from "@/components/nous/nav";
import { nousFetch, nousStream } from "@/lib/nous-api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "NOUS AI OS — Dashboard & Chat workspace" },
      {
        name: "description",
        content:
          "Το workspace του NOUS AI OS: chat με τον agent, missions, brain & memory, app builder, documents και έλεγχος συστήματος σε μία οθόνη.",
      },
      { property: "og:title", content: "NOUS AI OS — Dashboard" },
      {
        property: "og:description",
        content: "Chat, missions, μνήμη, app builder και έλεγχος συστήματος σε ένα workspace.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

// Δείγμα δεδομένων — αντικατέστησέ τα με πραγματικές κλήσεις στο /remote/* API.
const snapshot = [
  { k: "Health", v: "online", tone: "ok" as const },
  { k: "Autonomy", v: "active" },
  { k: "Missions σε εξέλιξη", v: "3" },
  { k: "Μνήμη", v: "12.4k εγγραφές" },
  { k: "Τελευταίο backup", v: "πριν 2 ώρες" },
];

const capabilities = [
  "chat brain",
  "missions",
  "self-healing",
  "app builder",
  "browser operator",
  "android operator",
  "documents",
  "scheduler",
];

const missions = [
  { title: "Καθαρισμός διπλών agent modules", status: "running" },
  { title: "Ανάλυση εγγράφου SF Caching", status: "queued" },
  { title: "Backup brain state", status: "done" },
];

const initiatives = [
  {
    title: "Να ενοποιήσω τα autonomy modules σε ένα core",
    why: "Βρήκα 9 παρόμοια αρχεία με επικαλυπτόμενη λογική.",
  },
  {
    title: "Να στήσω ημερήσιο backup στις 04:00",
    why: "Το τελευταίο backup έγινε χειροκίνητα.",
  },
];

const commandSignals = [
  { label: "Brain", value: "Ready", detail: "context indexed", tone: "text-ok", icon: Sparkles },
  { label: "Missions", value: "03", detail: "1 running now", tone: "text-primary", icon: Activity },
  { label: "Memory", value: "12.4k", detail: "synced 2m ago", tone: "text-signal", icon: ScanLine },
  {
    label: "Guard",
    value: "Armed",
    detail: "approval required",
    tone: "text-warn",
    icon: ShieldCheck,
  },
];

const activityFeed = [
  { time: "now", text: "NOUS is ready for a new objective", kind: "signal" },
  { time: "02m", text: "Memory index synchronized", kind: "done" },
  { time: "08m", text: "Mission queue reviewed", kind: "queued" },
];

type Citation = { title: string; url: string; domain: string };
type ChatMessage = { role: "user" | "assistant"; text: string; citations?: Citation[] };

const initialChat: ChatMessage[] = [
  {
    role: "assistant",
    text: "Καλώς ήρθες. Είμαι ο NOUS. Μπορώ να συζητήσω φυσικά, να αναλύσω στόχους, να προτείνω βήματα και —όταν είναι συνδεδεμένο το backend— να εκτελέσω εγκεκριμένες ενέργειες. Δεν θα παρουσιάσω ποτέ μια πρόταση ως ολοκληρωμένη ενέργεια χωρίς επιβεβαίωση.",
  },
];

function answerLocally(input: string) {
  const text = input.toLocaleLowerCase("el-GR");

  if (
    /(τι μπορείς|τι μπορεις|τι πραγματικ|τι πραγματικ|δυνατότητ|δυνατοτητ|help|βοήθεια|βοηθεια)/.test(
      text,
    )
  ) {
    return "Μπορώ να διαχειριστώ τοπικά το workspace: να εμφανίσω τα missions, να εξηγήσω την κατάσταση του συστήματος, να ξεκινήσω ή να προγραμματίσω backup και να σε οδηγήσω στις ενότητες Chat, Missions, Memory και System. Δεν προσποιούμαι ότι εκτέλεσα εξωτερική ενέργεια χωρίς συνδεδεμένο backend.";
  }

  if (/(mission|αποστολ|τρέχ|τρεχ)/.test(text)) {
    return "Στο workspace υπάρχουν 3 καταχωρημένα missions: ένα running, ένα queued και το backup brain state ως done. Άνοιξε την ενότητα Missions για τις λεπτομέρειες και την πραγματική κατάσταση κάθε αποστολής.";
  }

  if (/(backup|αντίγραφο|αντιγραφο)/.test(text)) {
    return "Μπορώ να προετοιμάσω backup μόνο όταν είναι διαθέσιμος ο τοπικός NOUS backend. Αυτή τη στιγμή δεν θα ισχυριστώ ότι δημιουργήθηκε αρχείο: το UI λειτουργεί offline και εμφανίζει την κατάσταση χωρίς να εκτελεί filesystem ενέργειες.";
  }

  if (/(health|υγεία|υγεια|κατάσταση|κατασταση|status)/.test(text)) {
    return "Κατάσταση UI: online. Αυτός ο browser workspace λειτουργεί τοπικά, αλλά δεν υπάρχει ενεργή σύνδεση με τον Flask/NOUS backend. Για πραγματικά missions, μνήμη και backup χρειάζεται να τρέχει το backend service.";
  }

  if (/(chat|συνομιλ|workspace|πού|που|βρω)/.test(text)) {
    return "Είσαι ήδη στο Chat workspace. Από το μενού μπορείς να ανοίξεις Home, Missions, Memory και System. Σε κινητό, πάτησε το κουμπί του μενού επάνω αριστερά.";
  }

  return `Κατάλαβα το αίτημα: «${input.trim()}». Μπορώ να απαντήσω για τοπική κατάσταση, missions, backup και τις ενότητες του workspace. Για ενέργειες στον πραγματικό υπολογιστή χρειάζεται συνδεδεμένος NOUS backend.`;
}

function Dashboard() {
  const [section, setSection] = useState("chat");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [messages, setMessages] = useState(initialChat);
  const [draft, setDraft] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [researchMode, setResearchMode] = useState<"auto" | "off" | "deep">("auto");
  const [connectionMode, setConnectionMode] = useState<"connected" | "degraded" | null>(null);
  const [activeFocus, setActiveFocus] = useState("chat");
  const [approvedInitiatives, setApprovedInitiatives] = useState<string[]>([]);
  const [dismissedInitiatives, setDismissedInitiatives] = useState<string[]>([]);
  const [approvals, setApprovals] = useState<
    Array<{ id: string; tool: string; input: unknown; createdAt: string }>
  >([]);
  const [approvalStatus, setApprovalStatus] = useState<"idle" | "loading" | "error">("idle");
  const [systemStatus, setSystemStatus] = useState<{
    status: string;
    counts?: { missions: number; toolRuns: number };
    storage?: string;
  } | null>(null);
  const [liveMissions, setLiveMissions] = useState<
    Array<{ id: string; title: string; status: string }>
  >([]);
  const [liveStatus, setLiveStatus] = useState<"idle" | "connecting" | "connected">("idle");
  const [providerAction, setProviderAction] = useState<string | null>(null);
  const [sentinel, setSentinel] = useState<{
    score: number;
    findings: Array<{
      id: string;
      severity: "low" | "medium" | "high";
      title: string;
      detail: string;
      remediation: string;
    }>;
    checkedAt: string;
  } | null>(null);

  const connectMissionStream = async () => {
    if (liveStatus === "connecting" || liveStatus === "connected") return;
    setLiveStatus("connecting");
    try {
      const response = await nousStream("/api/missions/stream");
      if (!response.body) throw new Error("stream unavailable");
      setLiveStatus("connected");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const event of events) {
          const line = event.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;
          const data = JSON.parse(line.slice(6)) as { missions?: typeof liveMissions };
          setLiveMissions(data.missions ?? []);
        }
      }
    } catch {
      setLiveStatus("idle");
    }
  };

  const loadSystemStatus = async () => {
    try {
      const data = await nousFetch<typeof systemStatus>("/api/status");
      setSystemStatus(data);
    } catch {
      setSystemStatus({ status: "unavailable" });
    }
  };

  const loadApprovals = async () => {
    setApprovalStatus("loading");
    try {
      const data = await nousFetch<{ approvals?: typeof approvals }>("/api/approvals");
      setApprovals(data.approvals ?? []);
      setApprovalStatus("idle");
    } catch {
      setApprovalStatus("error");
    }
  };

  const resolveApproval = async (id: string, status: "approved" | "rejected") => {
    try {
      await nousFetch("/api/approvals", {
        method: "PATCH",
        body: JSON.stringify({ id, status }),
      });
    } catch {
      return;
    }
    if (status === "approved") {
      try {
        await nousFetch("/api/tools/execute", {
          method: "POST",
          body: JSON.stringify({ approvalId: id }),
        });
      } catch {
        setApprovalStatus("error");
      }
    }
    setApprovals((items) => items.filter((item) => item.id !== id));
  };

  const send = async () => {
    const text = draft.trim();
    if (!text || isThinking) return;
    const history = messages.slice(-10);
    setMessages((m) => [...m, { role: "user", text }]);
    setDraft("");
    setIsThinking(true);

    try {
      const data = await nousFetch<{
        answer?: string;
        human_answer?: string;
        response?: string;
        error?: string;
        mode?: "connected" | "degraded";
        researchUsed?: boolean;
        citations?: Array<{ title: string; url: string; domain: string }>;
      }>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: text, history, researchMode }),
      });
      const answer = data.human_answer ?? data.answer ?? data.response;
      if (!answer) throw new Error(data.error ?? "Chat unavailable");
      setConnectionMode(data.mode ?? "connected");
      const suffix =
        data.mode === "degraded"
          ? "\n\n[Περιορισμένη λειτουργία: δεν εκτελέστηκε ��ξωτερική ενέργεια.]"
          : data.researchUsed && data.citations?.length
            ? `\n\n[Πηγές: ${data.citations.map((citation) => citation.domain).join(", ")}]`
            : "";
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: `${answer}${suffix}`,
          citations: data.researchUsed ? data.citations : undefined,
        },
      ]);
    } catch (error) {
      console.error("[v0] Chat request failed", error);
      setConnectionMode("degraded");
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: "Δεν μπόρεσα να συνδεθώ τώρα με το AI. Δεν εκτελέστηκε εξωτερική ενέργεια. Δοκίμασε ξανά σε λίγο.",
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const go = (id: string) => {
    setSection(id);
    setMenuOpen(false);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background font-sans text-foreground">
      {/* Sidebar */}
      {menuOpen && (
        <button
          aria-label="Κλείσε το μενού"
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-40 bg-black/55 lg:hidden"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-card/95 transition-transform lg:static lg:translate-x-0 ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-start justify-between px-4 pb-3 pt-4">
          <div>
            <p className="font-display text-base font-bold tracking-tight">🧠 NOUS AI OS</p>
            <p className="mt-0.5 text-xs text-muted-foreground">Personal agent workspace</p>
          </div>
          <button
            onClick={() => setMenuOpen(false)}
            className="text-muted-foreground lg:hidden"
            aria-label="Κλείσε"
          >
            <X className="size-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2 pb-2">
          {navGroups
            .filter((g) => !g.advanced)
            .map((group, gi) => (
              <div key={group.title ?? gi}>
                {group.title && (
                  <p className="px-2.5 pb-1 pt-3 font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                    {group.title}
                  </p>
                )}
                {group.items.map((item) => (
                  <NavButton
                    key={item.id}
                    item={item}
                    active={section === item.id}
                    onClick={() => go(item.id)}
                  />
                ))}
                {gi === 0 && <div className="my-2 h-px bg-border" />}
              </div>
            ))}

          <div className="my-2 h-px bg-border" />
          <button
            onClick={() => setAdvancedOpen((o) => !o)}
            className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            ⋯ Προχωρημένα
            <span className="ml-auto text-[10px]">{advancedOpen ? "▾" : "▸"}</span>
          </button>
          {advancedOpen &&
            navGroups
              .filter((g) => g.advanced)
              .map((group) => (
                <div key={group.title}>
                  <p className="px-2.5 pb-1 pt-3 font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                    {group.title}
                  </p>
                  {group.items.map((item) => (
                    <NavButton
                      key={item.id}
                      item={item}
                      active={section === item.id}
                      onClick={() => go(item.id)}
                    />
                  ))}
                </div>
              ))}
        </nav>

        <div className="border-t border-border px-3 py-3">
          <StatBar label="CPU" pct={34} color="bg-violet" />
          <StatBar label="RAM" pct={61} color="bg-primary" />
        </div>
      </aside>

      {/* Main */}
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-border/70 bg-card/70 px-4 py-3 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMenuOpen(true)}
              className="rounded-md border border-border p-1.5 lg:hidden"
              aria-label="Άνοιξε το μενού"
            >
              <Menu className="size-4" />
            </button>
            <strong className="font-display text-sm">{navLabel(section)}</strong>
            <span
              className={`rounded-full border border-border px-2.5 py-0.5 font-mono text-xs ${systemStatus?.status === "degraded" || systemStatus?.status === "unavailable" ? "text-warn" : "text-ok"}`}
            >
              health: {systemStatus?.status ?? "checking"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-muted-foreground sm:block">
              Owner Mode
            </span>
            <Link
              to="/"
              className="rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-primary hover:bg-accent"
            >
              info
            </Link>
          </div>
        </header>

        {section === "chat" ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <div className="flex-1 overflow-y-auto p-4 md:p-6">
              <div className="mx-auto max-w-4xl">
                <div className="mb-6 flex items-start justify-between gap-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-primary">
                      <span className="size-1.5 rounded-full bg-primary shadow-[0_0_14px_var(--primary)]" />
                      Agent online · Owner workspace
                    </div>
                    <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
                      Τι αναλαμβ��νουμε σήμερα;
                    </h1>
                    <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                      Στόχοι, missions, browser operator και κώδικας — σε μία ενιαία ροή με έγκριση
                      πριν από κάθε ��ξωτερική ενέργεια.
                    </p>
                  </div>
                  <div className="hidden rounded-xl border border-border/70 bg-background/50 p-3 text-right sm:block">
                    <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                      Runtime
                    </p>
                    <p className="mt-1 text-sm font-semibold text-ok">Ready</p>
                  </div>
                </div>
                <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {commandSignals.map(({ icon: Icon, label, value, detail, tone }) => (
                    <button
                      key={label}
                      type="button"
                      onClick={() => {
                        const focus = label.toLowerCase();
                        setActiveFocus(focus);
                        if (focus === "guard") void loadApprovals();
                        if (focus === "system") void loadSystemStatus();
                        if (focus === "missions") void connectMissionStream();
                      }}
                      className={`group rounded-xl border p-3 text-left transition-all ${activeFocus === label.toLowerCase() ? "border-primary/60 bg-primary/10 shadow-[0_0_24px_oklch(0.68_0.19_292_/_12%)]" : "border-border/70 bg-card/60 hover:border-primary/40"}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
                          {label}
                        </span>
                        <Icon className={`size-3.5 ${tone}`} />
                      </div>
                      <p className={`mt-2 font-display text-lg font-semibold ${tone}`}>{value}</p>
                      <p className="mt-0.5 truncate text-[10px] text-muted-foreground">{detail}</p>
                    </button>
                  ))}
                </div>
                {activeFocus === "missions" && (
                  <div className="mb-5 rounded-2xl border border-primary/30 bg-primary/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold">Live mission progress</p>
                        <p className="text-xs text-muted-foreground">
                          Server-sent updates κάθε 3 δευτερόλεπτα.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void connectMissionStream()}
                        className="rounded-lg border border-primary/30 px-3 py-1.5 text-xs text-primary"
                      >
                        {liveStatus === "connected" ? "Live" : "Σύνδεση"}
                      </button>
                    </div>
                    <div className="mt-3 space-y-2">
                      {liveMissions.map((mission) => (
                        <div
                          key={mission.id}
                          className="flex items-center justify-between rounded-lg bg-card/70 px-3 py-2 text-xs"
                        >
                          <span>{mission.title}</span>
                          <span className="font-mono text-muted-foreground">{mission.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {activeFocus === "system" && (
                  <div className="mb-5 rounded-2xl border border-signal/30 bg-signal/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold">Runtime status</p>
                        <p className="text-xs text-muted-foreground">
                          Ζωντανή κατάσταση από το persisted NOUS runtime.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void loadSystemStatus()}
                        className="rounded-lg border border-signal/30 px-3 py-1.5 text-xs text-signal hover:bg-signal/10"
                      >
                        Ανανέωση
                      </button>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="rounded-lg bg-card/70 p-2">
                        <p className="text-muted-foreground">Status</p>
                        <p className="mt-1 font-semibold text-ok">
                          {systemStatus?.status ?? "loading"}
                        </p>
                      </div>
                      <div className="rounded-lg bg-card/70 p-2">
                        <p className="text-muted-foreground">Missions</p>
                        <p className="mt-1 font-semibold">
                          {systemStatus?.counts?.missions ?? "—"}
                        </p>
                      </div>
                      <div className="rounded-lg bg-card/70 p-2">
                        <p className="text-muted-foreground">Tool runs</p>
                        <p className="mt-1 font-semibold">
                          {systemStatus?.counts?.toolRuns ?? "—"}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                {activeFocus === "guard" && (
                  <div className="mb-5 rounded-2xl border border-warn/30 bg-warn/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <ShieldAlert className="size-4 text-warn" />
                        <div>
                          <p className="text-sm font-semibold">Approval queue</p>
                          <p className="text-xs text-muted-foreground">
                            Καμία εξωτερική ενέργεια χωρίς δική σου έγκριση.
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void loadApprovals()}
                        className="rounded-lg border border-warn/30 px-3 py-1.5 text-xs text-warn hover:bg-warn/10"
                      >
                        {approvalStatus === "loading" ? "Έλεγχος…" : "Ανανέωση"}
                      </button>
                    </div>
                    {approvalStatus === "error" && (
                      <p className="mt-3 text-xs text-destructive">
                        Η approval queue δεν είναι διαθέσιμη.
                      </p>
                    )}
                    {approvalStatus === "idle" && approvals.length === 0 && (
                      <p className="mt-3 text-xs text-muted-foreground">
                        Δεν υπάρχουν pending approvals.
                      </p>
                    )}
                    <div className="mt-3 space-y-2">
                      {approvals.map((approval) => (
                        <div
                          key={approval.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 bg-card/70 p-3"
                        >
                          <div>
                            <p className="font-mono text-xs text-foreground">{approval.tool}</p>
                            <p className="mt-1 text-[11px] text-muted-foreground">
                              Ζητήθηκε {new Date(approval.createdAt).toLocaleString("el-GR")}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => void resolveApproval(approval.id, "approved")}
                              className="rounded-md bg-ok/15 px-3 py-1.5 text-xs font-semibold text-ok"
                            >
                              Έγκριση
                            </button>
                            <button
                              type="button"
                              onClick={() => void resolveApproval(approval.id, "rejected")}
                              className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground"
                            >
                              Απόρριψη
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="mb-5 grid gap-3 lg:grid-cols-[1fr_250px]">
                  <div className="rounded-2xl border border-border/70 bg-card/50 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="size-3.5 text-primary" />
                        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                          Mission pulse
                        </span>
                      </div>
                      <span className="rounded-full border border-ok/30 bg-ok/10 px-2 py-0.5 font-mono text-[9px] text-ok">
                        LIVE
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex -space-x-1">
                        {["bg-primary", "bg-ok", "bg-warn", "bg-signal"].map((color, index) => (
                          <span
                            key={index}
                            className={`size-2.5 rounded-full border-2 border-card ${color} ${index === 0 ? "animate-pulse" : ""}`}
                          />
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Objective graph is stable{" "}
                        <span className="text-foreground">· 3 nodes active</span>
                      </p>
                    </div>
                    <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/8">
                      <div className="h-full w-[72%] rounded-full bg-gradient-to-r from-primary via-violet to-signal" />
                    </div>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-card/50 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Clock3 className="size-3.5 text-muted-foreground" />
                      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                        Recent signal
                      </span>
                    </div>
                    <div className="space-y-2">
                      {activityFeed.map((event) => (
                        <div key={event.time} className="flex gap-2 text-[10px]">
                          <span className="w-7 shrink-0 font-mono text-muted-foreground/60">
                            {event.time}
                          </span>
                          <CheckCircle2 className="mt-0.5 size-3 shrink-0 text-ok" />
                          <span className="text-muted-foreground">{event.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {[
                    { icon: Sparkles, label: "Ask brain", prompt: "Τι μπορείς να κάνεις;" },
                    { icon: Activity, label: "Missions", prompt: "Δείξε μου τα missions" },
                    { icon: ArrowUpRight, label: "Browser", prompt: "Έλεγξε τον browser operator" },
                    {
                      icon: ShieldCheck,
                      label: "System",
                      prompt: "Ποια είναι η κατάσταση του συστήματος;",
                    },
                  ].map(({ icon: Icon, label, prompt }) => (
                    <button
                      key={label}
                      type="button"
                      onClick={() => setDraft(prompt)}
                      className="group flex items-center gap-2 rounded-xl border border-border/70 bg-card/60 px-3 py-2.5 text-left text-xs transition-colors hover:border-primary/50 hover:bg-primary/8"
                    >
                      <Icon className="size-3.5 text-primary transition-transform group-hover:scale-110" />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
                <div className="flex flex-col gap-3">
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={`whitespace-pre-wrap rounded-2xl border border-border p-4 text-sm leading-relaxed ${
                        m.role === "user" ? "self-end bg-violet/15" : "bg-card/80"
                      }`}
                    >
                      {m.text}
                      {m.citations && m.citations.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2 border-t border-border/60 pt-3">
                          {m.citations.map((citation) => (
                            <a
                              key={citation.url}
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex max-w-full items-center gap-1 rounded-md border border-signal/25 bg-signal/5 px-2 py-1 text-[10px] text-signal transition-colors hover:bg-signal/15"
                              title={citation.title}
                            >
                              <ArrowUpRight className="size-3 shrink-0" />
                              <span className="truncate">{citation.domain}</span>
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="border-t border-border/70 bg-card/75 p-4 backdrop-blur-xl">
              <div className="mx-auto mb-2 flex max-w-3xl items-center justify-between text-[11px] text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span>
                    {isThinking
                      ? researchMode === "deep"
                        ? "Αναζήτηση → σύνθεση…"
                        : "Ο ΝΟΥΣ σκέφτεται…"
                      : connectionMode === "degraded"
                        ? "Περιορισμένη λειτουργία"
                        : "Έτοιμος για μήνυμα"}
                  </span>
                  <label className="flex items-center gap-1 rounded-md border border-border/70 px-2 py-1">
                    <span className="sr-only">Research mode</span>
                    <select
                      value={researchMode}
                      onChange={(event) =>
                        setResearchMode(event.target.value as "auto" | "off" | "deep")
                      }
                      className="bg-transparent text-[10px] outline-none"
                    >
                      <option value="auto">Research: Auto</option>
                      <option value="deep">Research: Deep</option>
                      <option value="off">Research: Off</option>
                    </select>
                  </label>
                </div>
                <button
                  type="button"
                  onClick={() => setMessages(initialChat)}
                  disabled={isThinking || messages.length <= 1}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Καθαρισμός συνομιλίας"
                >
                  <RotateCcw className="size-3" /> Καθαρισμός
                </button>
              </div>
              <div className="mx-auto flex max-w-3xl gap-2">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" &&
                      !e.shiftKey &&
                      !e.nativeEvent.isComposing &&
                      e.keyCode !== 229
                    ) {
                      e.preventDefault();
                      void send();
                    }
                  }}
                  rows={2}
                  placeholder="Γράψε στον ΝΟΥΣ…"
                  className="flex-1 resize-none rounded-xl border border-input bg-background p-3 text-sm outline-none focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => void send()}
                  disabled={isThinking || !draft.trim()}
                  className="inline-flex items-center gap-2 rounded-xl bg-violet px-4 text-sm font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label={isThinking ? "Ο ΝΟΥΣ σκέφτεται" : "Στείλε μήνυμα"}
                >
                  {isThinking ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Send className="size-4" />
                  )}
                  <span className="hidden sm:inline">{isThinking ? "Σκέψη…" : "Στείλε"}</span>
                </button>
              </div>
            </div>
          </div>
        ) : section === "home" ? (
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <div className="rounded-2xl border border-border bg-gradient-to-br from-violet/20 to-primary/10 p-5">
              <h1 className="font-display text-2xl font-bold">Καλώς ήρθες στον ΝΟΥΣ</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Agent chat + workspace + Android companion + deploy, σε μία οθόνη.
              </p>
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <Card title="System Snapshot">
                {snapshot.map((r) => (
                  <div
                    key={r.k}
                    className="flex justify-between border-b border-border/60 py-1.5 text-sm last:border-0"
                  >
                    <span className="text-muted-foreground">{r.k}</span>
                    <span className={r.tone === "ok" ? "text-ok" : ""}>{r.v}</span>
                  </div>
                ))}
              </Card>

              <Card title="Capabilities">
                <div className="flex flex-wrap gap-2">
                  {capabilities.map((c) => (
                    <span
                      key={c}
                      className="rounded-full border border-border px-2.5 py-1 font-mono text-xs text-muted-foreground"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </Card>

              <Card title="Missions">
                {missions.map((m) => (
                  <div
                    key={m.title}
                    className="flex items-center justify-between gap-3 border-b border-border/60 py-2 text-sm last:border-0"
                  >
                    <span>{m.title}</span>
                    <span
                      className={`font-mono text-xs ${
                        m.status === "running"
                          ? "text-primary"
                          : m.status === "done"
                            ? "text-ok"
                            : "text-warn"
                      }`}
                    >
                      {m.status}
                    </span>
                  </div>
                ))}
              </Card>

              <Card title="Companion">
                <p className="text-sm text-muted-foreground">
                  Android companion: συνδεδεμένο · accessibility service ενεργό · 4 ασφαλείς εντολές
                  διαθέσιμες.
                </p>
              </Card>
            </div>

            <div className="mt-4 rounded-2xl border border-violet/40 bg-violet/5 p-5">
              <h3 className="font-display text-base font-semibold">🤖 Τι θέλει να κάνει ο ΝΟΥΣ</h3>
              <p className="text-xs text-muted-foreground">
                Α��τόνομες προτάσεις — έγκρινε ή απόρριψε
              </p>
              <div className="mt-4 space-y-3">
                {initiatives.map((i) => {
                  const approved = approvedInitiatives.includes(i.title);
                  const dismissed = dismissedInitiatives.includes(i.title);
                  if (dismissed) return null;
                  return (
                    <div
                      key={i.title}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4"
                    >
                      <div>
                        <p className="text-sm font-medium">{i.title}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{i.why}</p>
                        {approved && (
                          <p className="mt-2 font-mono text-[11px] text-ok">
                            Εγκρίθηκε και μπήκε στα missions
                          </p>
                        )}
                      </div>
                      {!approved && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => setApprovedInitiatives((items) => [...items, i.title])}
                            className="rounded-md bg-ok/20 px-3 py-1.5 text-xs font-semibold text-ok"
                          >
                            Έγκριση
                          </button>
                          <button
                            onClick={() => setDismissedInitiatives((items) => [...items, i.title])}
                            className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground"
                          >
                            Απόρριψη
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <div className="mx-auto grid max-w-5xl gap-4 lg:grid-cols-[1.3fr_0.7fr]">
              <Card title={navLabel(section)}>
                <p className="text-sm text-muted-foreground">
                  {section === "missions"
                    ? "Οι αποστολές εκτελούνται με checkpoints, logs και έγκριση πριν από κάθε επικίνδυνη ενέργεια."
                    : section === "memory"
                      ? "Η μνήμη του agent κρατά στόχους, αποφάσεις και συμπεράσματα με σαφή προέλευση."
                      : section === "system"
                        ? "Ο ΝΟΥΣ λειτουργεί με ασφαλή όρια: δεν ισχυρίζεται ότι έκανε κάτι αν δεν υπάρχει αποτέλεσμα από backend."
                        : `Η ενότητα ${navLabel(section)} είναι έτοιμη για σύνδεση με το NOUS API.`}
                </p>
                {section === "control" && (
                  <div className="mt-5 space-y-4">
                    <div className="rounded-2xl border border-primary/25 bg-primary/5 p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary">
                            NOUS control plane
                          </p>
                          <h2 className="mt-2 font-display text-xl font-semibold">
                            Οι συνδέσεις σου, με όρια που ελέγχεις
                          </h2>
                          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                            Ο NOUS μπορεί να χρησιμοποιεί model providers και repositories, αλλά
                            κάθε εξωτερική αλλαγή παραμένει proposal-first και απαιτεί ρητή έγκριση.
                          </p>
                        </div>
                        <span className="rounded-full border border-ok/30 bg-ok/10 px-2 py-1 font-mono text-[10px] text-ok">
                          GUARD ARMED
                        </span>
                      </div>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                      {[
                        {
                          name: "Google Gemini",
                          detail: "Per-user OAuth · model reasoning",
                          tone: "text-signal",
                          scope: "Μόνο εγκεκριμένες κλήσεις",
                        },
                        {
                          name: "ChatGPT / OpenAI",
                          detail: "Gateway provider · shared runtime",
                          tone: "text-ok",
                          scope: "Tokens server-side",
                        },
                        {
                          name: "GitHub",
                          detail: "Repos · branches · pull requests",
                          tone: "text-primary",
                          scope: "Push/merge πάντα με approval",
                        },
                      ].map((provider) => (
                        <div
                          key={provider.name}
                          className="rounded-2xl border border-border bg-card/60 p-4"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className={`size-2 rounded-full bg-current ${provider.tone}`} />
                            <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground">
                              AVAILABLE
                            </span>
                          </div>
                          <p className="mt-4 font-semibold">{provider.name}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{provider.detail}</p>
                          <p className="mt-3 rounded-lg bg-background/60 px-2 py-1.5 text-[11px] text-muted-foreground">
                            {provider.scope}
                          </p>
                          <button
                            type="button"
                            onClick={() => setProviderAction(provider.name)}
                            className="mt-3 w-full rounded-lg border border-border px-3 py-2 text-xs font-semibold transition-colors hover:border-primary/50 hover:bg-primary/5"
                          >
                            {providerAction === provider.name
                              ? "Έτοιμο για authorization flow"
                              : "Διαχείριση σύνδεσης"}
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="rounded-2xl border border-primary/25 bg-primary/5 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2 font-semibold">
                            <ScanLine className="size-4 text-primary" /> Defensive Sentinel
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Ελέγχει μόνο defensive controls του NOUS· δεν κάνει exploit ή scanning
                            τρίτων.
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              setSentinel(await nousFetch<typeof sentinel>("/api/security-audit"));
                            } catch {
                              setSentinel(null);
                            }
                          }}
                          className="rounded-lg border border-primary/30 px-3 py-2 text-xs font-semibold hover:bg-primary/10"
                        >
                          Έλεγχος τώρα
                        </button>
                      </div>
                      {sentinel && (
                        <div className="mt-4 grid gap-3 md:grid-cols-[auto_1fr]">
                          <div className="flex size-20 flex-col items-center justify-center rounded-full border-4 border-primary/40">
                            <strong className="text-xl">{sentinel.score}</strong>
                            <span className="font-mono text-[9px] text-muted-foreground">
                              / 100
                            </span>
                          </div>
                          <div className="space-y-2">
                            {sentinel.findings.length === 0 ? (
                              <p className="rounded-lg bg-ok/10 p-3 text-xs text-ok">
                                Όλα τα ενεργά defensive checks είναι εντάξει.
                              </p>
                            ) : (
                              sentinel.findings.map((finding) => (
                                <div
                                  key={finding.id}
                                  className="rounded-lg border border-border bg-background/60 p-3"
                                >
                                  <div className="flex items-center justify-between gap-2">
                                    <strong className="text-xs">{finding.title}</strong>
                                    <span className="font-mono text-[9px] uppercase text-muted-foreground">
                                      {finding.severity}
                                    </span>
                                  </div>
                                  <p className="mt-1 text-[11px] text-muted-foreground">
                                    {finding.detail}
                                  </p>
                                  <p className="mt-1 text-[11px] text-primary">
                                    Fix: {finding.remediation}
                                  </p>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="rounded-2xl border border-warn/25 bg-warn/5 p-4 text-sm">
                      <div className="flex items-center gap-2 font-semibold text-warn">
                        <ShieldAlert className="size-4" /> Action policy
                      </div>
                      <p className="mt-2 text-xs leading-5 text-muted-foreground">
                        Read operations μπορούν να προταθούν αυτόματα. Commit, push, merge, delete
                        και external side effects δημιουργούν approval record, diff και audit event
                        πριν εκτελεστούν.
                      </p>
                    </div>
                  </div>
                )}
                <div className="mt-5 space-y-2">
                  {section === "missions" &&
                    missions.map((mission) => (
                      <div
                        key={mission.title}
                        className="flex items-center justify-between rounded-xl border border-border bg-background/50 p-3 text-sm"
                      >
                        <span>{mission.title}</span>
                        <span className="font-mono text-xs text-primary">{mission.status}</span>
                      </div>
                    ))}
                  {section === "memory" &&
                    [
                      "User goals: autonomous NOUS",
                      "Decision: require approvals",
                      "Last reflection: backend-aware answers",
                    ].map((item) => (
                      <div
                        key={item}
                        className="rounded-xl border border-border bg-background/50 p-3 font-mono text-xs text-muted-foreground"
                      >
                        {item}
                      </div>
                    ))}
                </div>
              </Card>
              <Card title="Agent guardrails">
                <div className="space-y-3 text-sm">
                  {[
                    "Backend truth checks",
                    "Approval before side effects",
                    "Audit trail enabled",
                    "Browser operator: ready",
                  ].map((item) => (
                    <div key={item} className="flex items-center gap-2">
                      <span className="size-2 rounded-full bg-ok" />
                      {item}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function NavButton({
  item,
  active,
  onClick,
}: {
  item: { icon: string; label: string };
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`my-0.5 flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors ${
        active
          ? "bg-violet/20 font-semibold text-foreground"
          : "text-muted-foreground hover:bg-violet/10 hover:text-foreground"
      }`}
    >
      <span className="w-5 text-center text-base">{item.icon}</span>
      {item.label}
    </button>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5">
      <h3 className="mb-3 font-display text-base font-semibold">{title}</h3>
      {children}
    </section>
  );
}

function StatBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="flex items-center gap-2 py-1 font-mono text-[11px] text-muted-foreground">
      <span className="w-8">{label}</span>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span>{pct}%</span>
    </div>
  );
}
