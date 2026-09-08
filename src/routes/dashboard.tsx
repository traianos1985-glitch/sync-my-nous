import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Menu, Send, X } from "lucide-react";
import { navGroups, navLabel } from "@/components/nous/nav";

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

const initialChat = [
  {
    role: "assistant" as const,
    text: "Καλώς ήρθες. Είμαι σε λειτουργία Owner Mode. Τι θέλεις να αναλάβω;",
  },
  { role: "user" as const, text: "Δες τι missions τρέχουν και κάνε backup." },
  {
    role: "assistant" as const,
    text: "Τρέχουν 3 missions. Το backup ξεκίνησε — θα σε ενημερώσω όταν ολοκληρωθεί.",
  },
];

function Dashboard() {
  const [section, setSection] = useState("chat");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [messages, setMessages] = useState(initialChat);
  const [draft, setDraft] = useState("");

  const send = () => {
    const text = draft.trim();
    if (!text) return;
    setMessages((m) => [
      ...m,
      { role: "user", text },
      {
        role: "assistant",
        text: "Το κατέγραψα. (Σύνδεσε το NOUS API για πραγματικές απαντήσεις.)",
      },
    ]);
    setDraft("");
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
        <header className="flex items-center justify-between gap-3 border-b border-border bg-card/60 px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMenuOpen(true)}
              className="rounded-md border border-border p-1.5 lg:hidden"
              aria-label="Άνοιξε το μενού"
            >
              <Menu className="size-4" />
            </button>
            <strong className="font-display text-sm">{navLabel(section)}</strong>
            <span className="rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-ok">
              health: ok
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
              <div className="mx-auto flex max-w-3xl flex-col gap-3">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className={`whitespace-pre-wrap rounded-2xl border border-border p-4 text-sm leading-relaxed ${
                      m.role === "user" ? "self-end bg-violet/15" : "bg-card/80"
                    }`}
                  >
                    {m.text}
                  </div>
                ))}
              </div>
            </div>
            <div className="border-t border-border bg-card/60 p-4">
              <div className="mx-auto flex max-w-3xl gap-2">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  rows={2}
                  placeholder="Γράψε στον ΝΟΥΣ…"
                  className="flex-1 resize-none rounded-xl border border-input bg-background p-3 text-sm outline-none focus:border-primary"
                />
                <button
                  onClick={send}
                  className="inline-flex items-center gap-2 rounded-xl bg-violet px-4 text-sm font-semibold text-white"
                >
                  <Send className="size-4" />
                  <span className="hidden sm:inline">Στείλε</span>
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
                Αυτόνομες προτάσεις — έγκρινε ή απόρριψε
              </p>
              <div className="mt-4 space-y-3">
                {initiatives.map((i) => (
                  <div
                    key={i.title}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4"
                  >
                    <div>
                      <p className="text-sm font-medium">{i.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{i.why}</p>
                    </div>
                    <div className="flex gap-2">
                      <button className="rounded-md bg-ok/20 px-3 py-1.5 text-xs font-semibold text-ok">
                        Έγκριση
                      </button>
                      <button className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground">
                        Απόρριψη
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <Card title={navLabel(section)}>
              <p className="text-sm text-muted-foreground">
                Αυτή η ενότητα είναι έτοιμη για περιεχόμενο. Πες μου τι θέλεις να δείχνει το «
                {navLabel(section)}» και το φτιάχνω με τα δεδομένα του NOUS API.
              </p>
              <pre className="mt-4 overflow-x-auto rounded-lg border border-border bg-background p-4 font-mono text-xs text-muted-foreground">
                <code>{`GET /remote/${section}/status
X-NOUS-TOKEN: <token>`}</code>
              </pre>
            </Card>
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
