import { useRef, useState } from "react";
import { Plus, Play, Upload, Cloud, Rocket, Power } from "lucide-react";
import { actions, MODELS, useNous } from "@/lib/store";
import {
  Badge,
  Card,
  EmptyState,
  GhostButton,
  IconTrash,
  PrimaryButton,
  SectionHeader,
  Stat,
  TextInput,
  timeAgo,
} from "@/components/nous/ui";

const fmtSize = (b: number) => (b < 1024 ? `${b} B` : b < 1_048_576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1_048_576).toFixed(1)} MB`);

// ── Documents ─────────────────────────────────────────────────────────────────

export function DocumentsSection() {
  const { documents } = useNous();
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const upload = () => {
    actions.addDocument(name || "έγγραφο.txt", content);
    setName("");
    setContent("");
  };

  const onFile = async (file: File) => {
    const text = await file.text();
    actions.addDocument(file.name, text.slice(0, 200_000));
  };

  return (
    <div className="p-4 md:p-6">
      <SectionHeader
        title="Documents"
        subtitle="Ανέβασε έγγραφα, γίνονται chunk και ο agent μπορεί να απαντά πάνω τους."
        actions={
          <>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.md,.json,.csv,.log"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void onFile(f);
                e.target.value = "";
              }}
            />
            <PrimaryButton onClick={() => fileRef.current?.click()}>
              <Upload className="size-3.5" /> Ανέβασμα αρχείου
            </PrimaryButton>
          </>
        }
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <div className="space-y-2">
          {documents.length === 0 && <EmptyState text="Δεν υπάρχουν έγγραφα." />}
          {documents.map((d) => (
            <Card key={d.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-mono text-sm font-semibold">{d.name}</h3>
                  <div className="mt-1 flex flex-wrap gap-2">
                    <Badge tone="muted">{fmtSize(d.size)}</Badge>
                    <Badge tone="primary">{d.chunks} chunks</Badge>
                    <Badge tone="muted">{timeAgo(d.uploadedAt)}</Badge>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{d.content.slice(0, 240)}</p>
                </div>
                <IconTrash onClick={() => actions.removeDocument(d.id)} />
              </div>
            </Card>
          ))}
        </div>

        <Card title="Επικόλληση κειμένου" className="h-fit">
          <div className="space-y-3">
            <TextInput value={name} onChange={setName} placeholder="όνομα.md" />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={7}
              placeholder="Επικόλλησε το περιεχόμενο εδώ…"
              className="w-full resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            />
            <PrimaryButton onClick={upload} disabled={!content.trim()} className="w-full">
              <Plus className="size-3.5" /> Προσθήκη στη μνήμη
            </PrimaryButton>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Scheduler ─────────────────────────────────────────────────────────────────

export function SchedulerSection() {
  const { jobs } = useNous();
  const [name, setName] = useState("");
  const [cron, setCron] = useState("");

  const add = () => {
    actions.addJob(name, cron);
    setName("");
    setCron("");
  };

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Scheduler" subtitle="Cron jobs που τρέχουν αυτόνομα εργασίες σε τακτά διαστήματα." />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-2">
          {jobs.map((j) => (
            <Card key={j.id}>
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold">{j.name}</h3>
                    <Badge tone={j.enabled ? "ok" : "muted"}>{j.enabled ? "ενεργό" : "ανενεργό"}</Badge>
                  </div>
                  <p className="mt-1 font-mono text-xs text-muted-foreground">
                    {j.cron} · τελευταία: {timeAgo(j.lastRun)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <GhostButton onClick={() => actions.runJob(j.id)} title="Εκτέλεση τώρα">
                    <Play className="size-3" />
                  </GhostButton>
                  <GhostButton active={j.enabled} onClick={() => actions.toggleJob(j.id)} title="Ενεργοποίηση">
                    <Power className="size-3" />
                  </GhostButton>
                  <IconTrash onClick={() => actions.removeJob(j.id)} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        <Card title="Νέο job" className="h-fit">
          <div className="space-y-3">
            <TextInput value={name} onChange={setName} placeholder="Όνομα job" onEnter={add} />
            <TextInput value={cron} onChange={setCron} placeholder="Cron (π.χ. 0 4 * * *)" onEnter={add} />
            <PrimaryButton onClick={add} disabled={!name.trim()} className="w-full">
              <Plus className="size-3.5" /> Προσθήκη job
            </PrimaryButton>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Deploy ────────────────────────────────────────────────────────────────────

const TARGETS = [
  { id: "vps", name: "VPS (gunicorn)", cmd: "gunicorn executor.router:app" },
  { id: "docker", name: "Docker Compose", cmd: "docker compose up -d" },
  { id: "systemd", name: "systemd service", cmd: "systemctl restart nous" },
];

export function DeploySection() {
  const { activity } = useNous();
  const deployLog = activity.filter((a) => a.text.startsWith("Deploy"));

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Deploy" subtitle="Στόχοι deployment για το NOUS service." />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {TARGETS.map((t) => (
          <Card key={t.id}>
            <div className="flex items-center gap-2">
              <Rocket className="size-4 text-primary" />
              <h3 className="text-sm font-semibold">{t.name}</h3>
            </div>
            <pre className="mt-3 overflow-x-auto rounded-lg border border-border bg-background p-3 font-mono text-[11px] text-muted-foreground">
              <code>{t.cmd}</code>
            </pre>
            <PrimaryButton
              onClick={() => actions.runModule("deploy", `Deploy → ${t.name}`)}
              className="mt-3 w-full"
            >
              <Rocket className="size-3.5" /> Deploy
            </PrimaryButton>
          </Card>
        ))}
      </div>

      <Card title="Ιστορικό deployments" className="mt-4">
        {deployLog.length === 0 ? (
          <EmptyState text="Κανένα deployment ακόμη." />
        ) : (
          <div className="space-y-1.5">
            {deployLog.map((a) => (
              <div key={a.id} className="flex justify-between font-mono text-xs text-muted-foreground">
                <span>{a.text}</span>
                <span>{timeAgo(a.at)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

// ── Backup ─────────────────────────────────────────────────────────────────────

export function BackupSection() {
  const { backups } = useNous();

  return (
    <div className="p-4 md:p-6">
      <SectionHeader
        title="Backup"
        subtitle="Στιγμιότυπα του brain state — αυτόματα και χειροκίνητα."
        actions={
          <PrimaryButton onClick={() => actions.runBackup()}>
            <Cloud className="size-3.5" /> Backup τώρα
          </PrimaryButton>
        }
      />
      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Stat label="Σύνολο backups" value={backups.length} />
        <Stat label="Τελευταίο" value={timeAgo(backups[0]?.at ?? null)} tone="ok" />
        <Stat label="Συνολικός όγκος" value={`${backups.length * 46} MB`} />
      </div>
      <Card title="Ιστορικό">
        <div className="space-y-2">
          {backups.map((b) => (
            <div key={b.id} className="flex items-center justify-between border-b border-border/50 py-2 text-sm last:border-0">
              <div className="flex items-center gap-3">
                <Cloud className="size-4 text-muted-foreground" />
                <span className="font-mono text-xs">{new Date(b.at).toLocaleString("el-GR")}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="muted">{b.size}</Badge>
                <Badge tone={b.kind === "auto" ? "primary" : "violet"}>{b.kind}</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ── Settings ─────────────────────────────────────────────────────────────────

function Toggle({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3">
      <span className="text-sm">{label}</span>
      <button
        onClick={onClick}
        className={`relative h-6 w-11 rounded-full transition-colors ${on ? "bg-primary" : "bg-muted"}`}
        aria-pressed={on}
        aria-label={label}
      >
        <span
          className={`absolute top-0.5 size-5 rounded-full bg-white transition-transform ${on ? "translate-x-5" : "translate-x-0.5"}`}
        />
      </button>
    </div>
  );
}

export function SettingsSection() {
  const { settings } = useNous();

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Settings" subtitle="Ρυθμίσεις του agent, μοντέλο AI και ασφάλεια." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Agent">
          <div className="space-y-3">
            <Toggle label="Owner Mode" on={settings.ownerMode} onClick={() => actions.updateSettings({ ownerMode: !settings.ownerMode })} />
            <Toggle label="Αυτονομία (autonomy loop)" on={settings.autonomy} onClick={() => actions.updateSettings({ autonomy: !settings.autonomy })} />
            <Toggle label="Streaming απαντήσεις" on={settings.streaming} onClick={() => actions.updateSettings({ streaming: !settings.streaming })} />
          </div>
        </Card>

        <Card title="Μοντέλο AI">
          <p className="mb-3 text-sm text-muted-foreground">
            Το chat χρησιμοποιεί το Vercel AI Gateway. Διάλεξε μοντέλο:
          </p>
          <div className="space-y-2">
            {MODELS.map((m) => (
              <button
                key={m}
                onClick={() => actions.updateSettings({ model: m })}
                className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left font-mono text-xs transition-colors ${
                  settings.model === m
                    ? "border-primary/60 bg-primary/10 text-primary"
                    : "border-border bg-background text-muted-foreground hover:bg-accent"
                }`}
              >
                {m}
                {settings.model === m && <Badge tone="primary">ενεργό</Badge>}
              </button>
            ))}
          </div>
        </Card>

        <Card title="Ασφάλεια">
          <p className="mb-3 text-sm text-muted-foreground">
            Fail-closed auth: κάθε endpoint θέλει token. Όρισε το access token για απομακρυσμένη πρόσβαση.
          </p>
          <TextInput
            value={settings.apiToken}
            onChange={(v) => actions.updateSettings({ apiToken: v })}
            placeholder="X-NOUS-TOKEN"
          />
        </Card>

        <Card title="Δεδομένα">
          <p className="mb-3 text-sm text-muted-foreground">
            Όλα τα δεδομένα του workspace αποθηκεύονται τοπικά στον browser σου.
          </p>
          <GhostButton onClick={() => { if (confirm("Επαναφορά όλων των δεδομένων;")) actions.resetAll(); }}>
            Επαναφορά όλων των δεδομένων
          </GhostButton>
        </Card>
      </div>
    </div>
  );
}
