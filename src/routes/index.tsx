import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  ArrowUpRight,
  Boxes,
  Brain,
  CircuitBoard,
  Cpu,
  FileSearch,
  Github,
  Globe,
  Hammer,
  Layers,
  Lock,
  Smartphone,
  Sparkles,
  Terminal,
  Wrench,
} from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "NOUS AI OS — Αυτόνομος AI agent σε Python & Flask" },
      {
        name: "description",
        content:
          "NOUS AI OS: αυτόνομο AI λειτουργικό σύστημα με chat brain, μνήμη, missions, self-healing, app builder και Android operator — όλα σε ένα service.",
      },
      { property: "og:title", content: "NOUS AI OS — Αυτόνομος AI agent" },
      {
        property: "og:description",
        content:
          "Chat brain, μνήμη, missions, self-healing, app builder, browser & Android operators και document intelligence σε ένα service.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const REPO = "https://github.com/traianos1985-glitch/Nous-AI-OS";

const stats = [
  { value: "~300", label: "modules στο executor" },
  { value: "351", label: "HTTP routes" },
  { value: "1", label: "service για όλα" },
  { value: "fail-closed", label: "auth by default" },
];

const capabilities = [
  {
    icon: Brain,
    title: "Chat brain & μνήμη",
    text: "Συνομιλία με επίμονη μνήμη, conversation index και decision memory που μαθαίνει από τα λάθη του.",
  },
  {
    icon: Activity,
    title: "Missions & autonomy",
    text: "Scheduler, executor και journal για αποστολές που τρέχουν μόνες τους στο background.",
  },
  {
    icon: Wrench,
    title: "Self-healing",
    text: "Auto-repair, code analysis και repair proposals: εντοπίζει βλάβες και προτείνει διορθώσεις.",
  },
  {
    icon: Hammer,
    title: "App builder",
    text: "App factory και evolver που γράφουν, τρέχουν και βελτιώνουν μικρές εφαρμογές μόνα τους.",
  },
  {
    icon: Globe,
    title: "Browser operator",
    text: "Αυτοματισμός περιήγησης για έρευνα, φόρμες και επαναλαμβανόμενες εργασίες στο web.",
  },
  {
    icon: Smartphone,
    title: "Android companion",
    text: "Kotlin app με accessibility service, ώστε ο agent να χειρίζεται πραγματικό κινητό.",
  },
  {
    icon: FileSearch,
    title: "Document intelligence",
    text: "Ανέβασμα, chunking και ερωτήσεις πάνω σε δικά σου έγγραφα και manuals.",
  },
  {
    icon: Lock,
    title: "Fail-closed ασφάλεια",
    text: "Κάθε endpoint θέλει token. Χωρίς token, μόνο localhost. Τα δεδομένα μένουν untracked.",
  },
];

const layers = [
  {
    icon: Terminal,
    name: "executor/router.py",
    text: "Flask API + dashboard, το μοναδικό σημείο εισόδου.",
  },
  {
    icon: Cpu,
    name: "brain / agents / engines",
    text: "Σκέψη, σχεδιασμός, εκτέλεση και αναθεώρηση αποστολών.",
  },
  {
    icon: CircuitBoard,
    name: "operators",
    text: "Browser και Android χειριστές για δράση στον έξω κόσμο.",
  },
  {
    icon: Boxes,
    name: "data / deploy",
    text: "Runtime κατάσταση, backups και scripts για VPS, Windows, macOS, Linux.",
  },
];

const upgrades = [
  {
    tag: "Προτεραιότητα 1",
    title: "Καθαρισμός διπλών agent modules",
    text: "Υπάρχουν πολλά παράλληλα autonomy/agent αρχεία (agent_v2, autonomous_v2, autonomy_v3…). Ένα ενιαίο core με plugins μειώνει δραστικά τα bugs.",
    tone: "alert" as const,
  },
  {
    tag: "Προτεραιότητα 1",
    title: "Ένα σύγχρονο web UI αντί dashboard μέσα στη Flask",
    text: "Ξεχωριστό frontend που μιλά με το API μέσω token: chat, missions, μνήμη, logs, έγγραφα σε πραγματικό χρόνο.",
    tone: "signal" as const,
  },
  {
    tag: "Προτεραιότητα 2",
    title: "Βάση δεδομένων στη θέση των JSON αρχείων",
    text: "Τα data/*.json δεν κλιμακώνουν και χαλάνε σε ταυτόχρονη εγγραφή. SQLite ή Postgres με migrations λύνει μνήμη, αναζήτηση και backup.",
    tone: "signal" as const,
  },
  {
    tag: "Προτεραιότητα 2",
    title: "Streaming απαντήσεις & queue για μεγάλες εργασίες",
    text: "Server-sent events για ζωντανό chat και ουρά εργασιών, ώστε οι αποστολές να μην μπλοκάρουν το HTTP request.",
    tone: "signal" as const,
  },
  {
    tag: "Προτεραιότητα 3",
    title: "Παρατηρησιμότητα & κόστος",
    text: "Κεντρικό log με tokens, χρόνο και κόστος ανά κλήση μοντέλου, με όρια ανά ημέρα.",
    tone: "muted" as const,
  },
  {
    tag: "Προτεραιότητα 3",
    title: "Πραγματικά tests αντί smoke",
    text: "Σενάρια για brain, missions και auth guard, ώστε το CI να πιάνει regressions πριν το deploy.",
    tone: "muted" as const,
  },
];

function Index() {
  return (
    <main className="min-h-screen bg-background font-sans text-foreground">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            backgroundImage:
              "linear-gradient(var(--color-grid) 1px, transparent 1px), linear-gradient(90deg, var(--color-grid) 1px, transparent 1px)",
            backgroundSize: "56px 56px",
            maskImage:
              "radial-gradient(circle at 30% 0%, black, transparent 70%)",
          }}
        />
        <div className="relative mx-auto max-w-6xl px-6 py-24 md:py-32">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 font-mono text-xs text-primary">
            <span className="size-1.5 animate-pulse rounded-full bg-primary" />
            status: online · fail-closed auth
          </div>

          <h1 className="mt-8 font-display text-5xl font-bold leading-[1.05] tracking-tight md:text-7xl">
            NOUS <span className="text-primary">AI OS</span>
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
            Αυτόνομος AI agent σε Python και Flask που λειτουργεί σαν λειτουργικό
            σύστημα: σκέφτεται, θυμάται, φτιάχνει εφαρμογές, επισκευάζει τον
            εαυτό του και χειρίζεται browser και κινητό — όλα από ένα service.
          </p>

          <div className="mt-10 flex flex-wrap gap-3">
            <a
              href={REPO}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-3 font-mono text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
            >
              <Github className="size-4" />
              Άνοιξε το repo
            </a>
            <a
              href="#quickstart"
              className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-5 py-3 font-mono text-sm text-foreground transition-colors hover:bg-accent"
            >
              <Terminal className="size-4" />
              Γρήγορη εκκίνηση
            </a>
            <a
              href="#upgrades"
              className="inline-flex items-center gap-2 rounded-md px-5 py-3 font-mono text-sm text-primary transition-colors hover:bg-accent"
            >
              <Sparkles className="size-4" />
              Προτάσεις αναβάθμισης
            </a>
          </div>

          <dl className="mt-16 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border md:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} className="bg-card px-5 py-6">
                <dt className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  {s.label}
                </dt>
                <dd className="mt-2 font-display text-2xl font-bold text-primary">
                  {s.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Capabilities */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="flex items-end justify-between gap-6">
          <h2 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
            Τι κάνει
          </h2>
          <span className="font-mono text-xs text-muted-foreground">
            /capabilities
          </span>
        </div>

        <div className="mt-12 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map(({ icon: Icon, title, text }) => (
            <article
              key={title}
              className="group bg-card p-6 transition-colors hover:bg-accent"
            >
              <Icon className="size-6 text-primary" />
              <h3 className="mt-4 font-display text-lg font-semibold">
                {title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {text}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section className="border-y border-border bg-card/40">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid gap-12 lg:grid-cols-[1fr_1.1fr]">
            <div>
              <h2 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
                Αρχιτεκτονική
              </h2>
              <p className="mt-4 max-w-md leading-relaxed text-muted-foreground">
                Ένα Flask service (<code className="font-mono text-primary">executor.router:app</code>)
                σηκώνει API, dashboard και όλους τους agents. Ο φάκελος{" "}
                <code className="font-mono text-primary">data/</code> κρατά την
                κατάσταση και μένει εκτός Git.
              </p>
              <div className="mt-8 flex items-center gap-2 font-mono text-xs text-muted-foreground">
                <Layers className="size-4 text-primary" />
                Python · Flask · Gunicorn · Docker · Kotlin
              </div>
            </div>

            <ol className="grid gap-px overflow-hidden rounded-lg border border-border bg-border">
              {layers.map(({ icon: Icon, name, text }, i) => (
                <li key={name} className="flex gap-4 bg-card p-6">
                  <span className="font-mono text-xs text-muted-foreground">
                    0{i + 1}
                  </span>
                  <Icon className="size-5 shrink-0 text-primary" />
                  <div>
                    <p className="font-mono text-sm text-foreground">{name}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      {/* Upgrades */}
      <section id="upgrades" className="mx-auto max-w-6xl px-6 py-24">
        <div className="flex items-end justify-between gap-6">
          <div>
            <h2 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
              Προτάσεις αναβάθμισης
            </h2>
            <p className="mt-3 max-w-xl text-muted-foreground">
              Έξι βελτιώσεις με σειρά προτεραιότητας, από τον έλεγχο του κώδικα
              και της δομής του project.
            </p>
          </div>
          <span className="hidden font-mono text-xs text-muted-foreground md:block">
            /roadmap
          </span>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-2">
          {upgrades.map((u) => (
            <article
              key={u.title}
              className="rounded-lg border border-border bg-card p-6 transition-colors hover:border-primary/50"
            >
              <span
                className={[
                  "font-mono text-xs uppercase tracking-wider",
                  u.tone === "alert"
                    ? "text-alert"
                    : u.tone === "signal"
                      ? "text-primary"
                      : "text-muted-foreground",
                ].join(" ")}
              >
                {u.tag}
              </span>
              <h3 className="mt-3 font-display text-xl font-semibold">
                {u.title}
              </h3>
              <p className="mt-2 leading-relaxed text-muted-foreground">
                {u.text}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* Quickstart */}
      <section
        id="quickstart"
        className="border-t border-border bg-card/40"
      >
        <div className="mx-auto max-w-6xl px-6 py-24">
          <h2 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
            Γρήγορη εκκίνηση
          </h2>
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            <pre className="overflow-x-auto rounded-lg border border-border bg-background p-6 font-mono text-sm leading-relaxed text-muted-foreground">
              <code>{`git clone ${REPO}.git
cd Nous-AI-OS
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # βάλε OPENROUTER_API_KEY
python -m executor.router # http://localhost:5000`}</code>
            </pre>
            <div className="rounded-lg border border-border bg-background p-6">
              <h3 className="font-display text-lg font-semibold">
                Production
              </h3>
              <pre className="mt-3 overflow-x-auto font-mono text-sm text-muted-foreground">
                <code>{`gunicorn --bind 0.0.0.0:5000 \\
  --workers 2 --timeout 120 \\
  executor.router:app

# ή
docker compose up -d`}</code>
              </pre>
              <p className="mt-6 text-sm leading-relaxed text-muted-foreground">
                Για πρόσβαση από κινητό ή έξω από το δίκτυο, φτιάξε token με{" "}
                <code className="font-mono text-primary">POST /token/create</code>{" "}
                και στείλ' το ως{" "}
                <code className="font-mono text-primary">X-NOUS-TOKEN</code>.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 font-mono text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>NOUS AI OS · traianos1985-glitch</p>
          <a
            href={REPO}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-primary hover:underline"
          >
            github.com/traianos1985-glitch/Nous-AI-OS
            <ArrowUpRight className="size-3" />
          </a>
        </div>
      </footer>
    </main>
  );
}
