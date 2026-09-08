import { useSyncExternalStore } from "react";

// ── Τύποι οντοτήτων ────────────────────────────────────────────────────────

export type ID = string;

export type Goal = {
  id: ID;
  title: string;
  detail: string;
  progress: number;
  status: "active" | "done" | "paused";
  createdAt: number;
};

export type Mission = {
  id: ID;
  title: string;
  status: "queued" | "running" | "done" | "failed";
  progress: number;
  log: string[];
  createdAt: number;
};

export type PlannerItem = {
  id: ID;
  title: string;
  when: string;
  priority: "low" | "med" | "high";
  done: boolean;
};

export type MemoryEntry = {
  id: ID;
  kind: "fact" | "decision" | "conversation";
  text: string;
  createdAt: number;
};

export type BuiltApp = {
  id: ID;
  name: string;
  description: string;
  status: "draft" | "building" | "live";
  createdAt: number;
};

export type NousDoc = {
  id: ID;
  name: string;
  size: number;
  chunks: number;
  content: string;
  uploadedAt: number;
};

export type Job = {
  id: ID;
  name: string;
  cron: string;
  enabled: boolean;
  lastRun: number | null;
};

export type Backup = {
  id: ID;
  at: number;
  size: string;
  kind: "auto" | "manual";
};

export type Approval = {
  id: ID;
  title: string;
  why: string;
  status: "pending" | "approved" | "rejected";
  createdAt: number;
};

export type Activity = {
  id: ID;
  at: number;
  level: "info" | "ok" | "warn" | "err";
  text: string;
};

export type ChatMessage = { id: ID; role: "user" | "assistant"; text: string };

export type ModuleState = { enabled: boolean; runs: number; lastRun: number | null };

export type Settings = {
  ownerMode: boolean;
  autonomy: boolean;
  streaming: boolean;
  model: string;
  apiToken: string;
};

export type State = {
  goals: Goal[];
  missions: Mission[];
  planner: PlannerItem[];
  memory: MemoryEntry[];
  apps: BuiltApp[];
  documents: NousDoc[];
  jobs: Job[];
  backups: Backup[];
  approvals: Approval[];
  activity: Activity[];
  chat: ChatMessage[];
  modules: Record<string, ModuleState>;
  settings: Settings;
};

// ── Αρχικά δεδομένα ─────────────────────────────────────────────────────────

const now = Date.now();
const h = 3_600_000;

const MODULE_IDS = [
  "autoexec",
  "loopv3",
  "autoscheduler",
  "diagnosis",
  "repair",
  "selfheal",
  "intelligence",
  "learning",
  "system",
  "command",
  "audit",
  "companion",
  "pending",
  "graphs",
  "analyst",
  "larmor",
  "field",
  "remote-access",
];

function seedModules(): Record<string, ModuleState> {
  const out: Record<string, ModuleState> = {};
  for (const id of MODULE_IDS) {
    out[id] = { enabled: ["autoexec", "selfheal", "system", "companion"].includes(id), runs: 0, lastRun: null };
  }
  return out;
}

const AVAILABLE_MODELS = [
  "anthropic/claude-sonnet-4.5",
  "anthropic/claude-haiku-4.5",
  "google/gemini-3.5-flash",
  "openai/gpt-5.1",
];

export const MODELS = AVAILABLE_MODELS;

function initialState(): State {
  return {
    goals: [
      {
        id: "g1",
        title: "Ενοποίηση autonomy modules σε ένα core",
        detail: "9 παρόμοια αρχεία με επικαλυπτόμενη λογική — ενοποίηση σε plugin architecture.",
        progress: 35,
        status: "active",
        createdAt: now - 40 * h,
      },
      {
        id: "g2",
        title: "Μετάβαση από JSON σε βάση δεδομένων",
        detail: "Τα data/*.json δεν κλιμακώνουν. Στόχος: SQLite/Postgres με migrations.",
        progress: 10,
        status: "active",
        createdAt: now - 20 * h,
      },
      {
        id: "g3",
        title: "Ημερήσιο αυτόματο backup 04:00",
        detail: "Scheduler job για backup του brain state κάθε βράδυ.",
        progress: 100,
        status: "done",
        createdAt: now - 72 * h,
      },
    ],
    missions: [
      {
        id: "m1",
        title: "Καθαρισμός διπλών agent modules",
        status: "running",
        progress: 62,
        log: ["Σάρωση 9 modules", "Εντοπίστηκαν 4 duplicates", "Ενοποίηση agent_v2 + autonomous_v2"],
        createdAt: now - 6 * h,
      },
      {
        id: "m2",
        title: "Ανάλυση εγγράφου SF Caching",
        status: "queued",
        progress: 0,
        log: ["Σε αναμονή για slot εκτέλεσης"],
        createdAt: now - 2 * h,
      },
      {
        id: "m3",
        title: "Backup brain state",
        status: "done",
        progress: 100,
        log: ["Snapshot 12.4k εγγραφών", "Συμπίεση", "Αποθήκευση στο data/backups"],
        createdAt: now - 26 * h,
      },
    ],
    planner: [
      { id: "p1", title: "Review pull request #42", when: "Σήμερα 14:00", priority: "high", done: false },
      { id: "p2", title: "Refactor executor/router.py", when: "Σήμερα 16:30", priority: "med", done: false },
      { id: "p3", title: "Δοκιμή Android companion εντολών", when: "Αύριο 10:00", priority: "med", done: false },
      { id: "p4", title: "Ενημέρωση requirements.txt", when: "Ολοκληρώθηκε", priority: "low", done: true },
    ],
    memory: [
      { id: "me1", kind: "fact", text: "Ο χρήστης προτιμά απαντήσεις στα Ελληνικά.", createdAt: now - 50 * h },
      { id: "me2", kind: "decision", text: "Χρήση fail-closed auth σε όλα τα endpoints.", createdAt: now - 30 * h },
      { id: "me3", kind: "fact", text: "Production τρέχει με gunicorn 2 workers, timeout 120s.", createdAt: now - 12 * h },
    ],
    apps: [
      { id: "a1", name: "log-viewer", description: "Μικρό UI για τα runtime logs.", status: "live", createdAt: now - 100 * h },
      { id: "a2", name: "token-manager", description: "CRUD για access tokens.", status: "building", createdAt: now - 5 * h },
    ],
    documents: [
      {
        id: "d1",
        name: "sf-caching.md",
        size: 18422,
        chunks: 14,
        content: "Οδηγός για caching στρατηγικές στο service.",
        uploadedAt: now - 3 * h,
      },
    ],
    jobs: [
      { id: "j1", name: "Ημερήσιο backup", cron: "0 4 * * *", enabled: true, lastRun: now - 26 * h },
      { id: "j2", name: "Health check", cron: "*/5 * * * *", enabled: true, lastRun: now - 5 * 60_000 },
      { id: "j3", name: "Καθαρισμός logs", cron: "0 0 * * 0", enabled: false, lastRun: now - 168 * h },
    ],
    backups: [
      { id: "b1", at: now - 26 * h, size: "48 MB", kind: "auto" },
      { id: "b2", at: now - 50 * h, size: "47 MB", kind: "auto" },
      { id: "b3", at: now - 74 * h, size: "45 MB", kind: "manual" },
    ],
    approvals: [
      {
        id: "ap1",
        title: "Να ενοποιήσω τα autonomy modules σε ένα core",
        why: "Βρήκα 9 παρόμοια αρχεία με επικαλυπτόμενη λογική.",
        status: "pending",
        createdAt: now - 4 * h,
      },
      {
        id: "ap2",
        title: "Να στήσω ημερήσιο backup στις 04:00",
        why: "Το τελευταίο backup έγινε χειροκίνητα.",
        status: "pending",
        createdAt: now - 3 * h,
      },
    ],
    activity: [
      { id: "ac1", at: now - 5 * 60_000, level: "ok", text: "Health check OK" },
      { id: "ac2", at: now - 6 * h, level: "info", text: "Mission «Καθαρισμός modules» ξεκίνησε" },
      { id: "ac3", at: now - 26 * h, level: "ok", text: "Αυτόματο backup ολοκληρώθηκε (48 MB)" },
    ],
    chat: [
      {
        id: "c0",
        role: "assistant",
        text: "Καλώς ήρθες. Είμαι ο ΝΟΥΣ σε λειτουργία Owner Mode. Ρώτησέ με ή δώσε μου μια εντολή — μπορώ να διαχειριστώ goals, missions, μνήμη, έγγραφα και το σύστημα.",
      },
    ],
    modules: seedModules(),
    settings: {
      ownerMode: true,
      autonomy: true,
      streaming: true,
      model: AVAILABLE_MODELS[0],
      apiToken: "",
    },
  };
}

// ── Store engine ────────────────────────────────────────────────────────────

const KEY = "nous-ai-os:v1";
let state: State = initialState();
let hydrated = false;
const listeners = new Set<() => void>();

function persist() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* quota or private mode — αγνόησέ το */
  }
}

function emit() {
  for (const l of listeners) l();
}

function set(updater: (s: State) => State) {
  state = updater(state);
  persist();
  emit();
}

const uid = () => Math.random().toString(36).slice(2, 10);

export function hydrate() {
  if (hydrated || typeof window === "undefined") return;
  hydrated = true;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<State>;
      // Merge ώστε νέα πεδία/modules να προστίθενται πάνω στα αποθηκευμένα.
      const base = initialState();
      state = {
        ...base,
        ...parsed,
        modules: { ...base.modules, ...(parsed.modules ?? {}) },
        settings: { ...base.settings, ...(parsed.settings ?? {}) },
      };
      emit();
    }
  } catch {
    /* corrupted storage — κράτα τα defaults */
  }
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

const getSnapshot = () => state;
const getServerSnapshot = () => state;

export function useNous(): State {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

// ── Actions ───────────────────────────────────────────────────────────────

export function logActivity(level: Activity["level"], text: string) {
  set((s) => ({
    ...s,
    activity: [{ id: uid(), at: Date.now(), level, text }, ...s.activity].slice(0, 60),
  }));
}

export const actions = {
  // Chat
  addChatMessage(role: ChatMessage["role"], text: string): ChatMessage {
    const msg: ChatMessage = { id: uid(), role, text };
    set((s) => ({ ...s, chat: [...s.chat, msg] }));
    return msg;
  },
  updateChatMessage(id: ID, text: string) {
    set((s) => ({ ...s, chat: s.chat.map((m) => (m.id === id ? { ...m, text } : m)) }));
  },
  clearChat() {
    set((s) => ({ ...s, chat: initialState().chat }));
    logActivity("info", "Το chat καθαρίστηκε");
  },

  // Goals
  addGoal(title: string, detail: string) {
    if (!title.trim()) return;
    set((s) => ({
      ...s,
      goals: [
        { id: uid(), title, detail, progress: 0, status: "active", createdAt: Date.now() },
        ...s.goals,
      ],
    }));
    logActivity("info", `Νέος στόχος: ${title}`);
  },
  setGoalProgress(id: ID, progress: number) {
    set((s) => ({
      ...s,
      goals: s.goals.map((g) =>
        g.id === id ? { ...g, progress, status: progress >= 100 ? "done" : g.status } : g,
      ),
    }));
  },
  removeGoal(id: ID) {
    set((s) => ({ ...s, goals: s.goals.filter((g) => g.id !== id) }));
  },

  // Missions
  addMission(title: string) {
    if (!title.trim()) return;
    set((s) => ({
      ...s,
      missions: [
        { id: uid(), title, status: "queued", progress: 0, log: ["Δημιουργήθηκε"], createdAt: Date.now() },
        ...s.missions,
      ],
    }));
    logActivity("info", `Νέο mission: ${title}`);
  },
  setMissionStatus(id: ID, status: Mission["status"]) {
    set((s) => ({
      ...s,
      missions: s.missions.map((m) =>
        m.id === id
          ? {
              ...m,
              status,
              progress: status === "done" ? 100 : status === "running" ? Math.max(m.progress, 5) : m.progress,
              log: [...m.log, `Κατάσταση → ${status}`],
            }
          : m,
      ),
    }));
    logActivity(status === "failed" ? "err" : "ok", `Mission ${status}`);
  },
  removeMission(id: ID) {
    set((s) => ({ ...s, missions: s.missions.filter((m) => m.id !== id) }));
  },

  // Planner
  addPlannerItem(title: string, when: string, priority: PlannerItem["priority"]) {
    if (!title.trim()) return;
    set((s) => ({
      ...s,
      planner: [{ id: uid(), title, when: when || "Χωρίς προθεσμία", priority, done: false }, ...s.planner],
    }));
  },
  togglePlanner(id: ID) {
    set((s) => ({
      ...s,
      planner: s.planner.map((p) => (p.id === id ? { ...p, done: !p.done } : p)),
    }));
  },
  removePlanner(id: ID) {
    set((s) => ({ ...s, planner: s.planner.filter((p) => p.id !== id) }));
  },

  // Memory
  addMemory(kind: MemoryEntry["kind"], text: string) {
    if (!text.trim()) return;
    set((s) => ({
      ...s,
      memory: [{ id: uid(), kind, text, createdAt: Date.now() }, ...s.memory],
    }));
    logActivity("info", "Νέα εγγραφή μνήμης");
  },
  removeMemory(id: ID) {
    set((s) => ({ ...s, memory: s.memory.filter((m) => m.id !== id) }));
  },

  // Apps
  addApp(name: string, description: string) {
    if (!name.trim()) return;
    set((s) => ({
      ...s,
      apps: [
        { id: uid(), name, description, status: "building", createdAt: Date.now() },
        ...s.apps,
      ],
    }));
    logActivity("info", `App factory: δημιουργία «${name}»`);
  },
  setAppStatus(id: ID, status: BuiltApp["status"]) {
    set((s) => ({ ...s, apps: s.apps.map((a) => (a.id === id ? { ...a, status } : a)) }));
    logActivity("ok", `App «${status}»`);
  },
  removeApp(id: ID) {
    set((s) => ({ ...s, apps: s.apps.filter((a) => a.id !== id) }));
  },

  // Documents
  addDocument(name: string, content: string) {
    if (!name.trim()) return;
    const size = new Blob([content]).size;
    set((s) => ({
      ...s,
      documents: [
        {
          id: uid(),
          name,
          size,
          chunks: Math.max(1, Math.ceil(content.length / 1200)),
          content,
          uploadedAt: Date.now(),
        },
        ...s.documents,
      ],
    }));
    logActivity("ok", `Έγγραφο ανέβηκε: ${name}`);
  },
  removeDocument(id: ID) {
    set((s) => ({ ...s, documents: s.documents.filter((d) => d.id !== id) }));
  },

  // Jobs
  addJob(name: string, cron: string) {
    if (!name.trim()) return;
    set((s) => ({
      ...s,
      jobs: [{ id: uid(), name, cron: cron || "0 * * * *", enabled: true, lastRun: null }, ...s.jobs],
    }));
  },
  toggleJob(id: ID) {
    set((s) => ({ ...s, jobs: s.jobs.map((j) => (j.id === id ? { ...j, enabled: !j.enabled } : j)) }));
  },
  runJob(id: ID) {
    set((s) => ({ ...s, jobs: s.jobs.map((j) => (j.id === id ? { ...j, lastRun: Date.now() } : j)) }));
    const job = state.jobs.find((j) => j.id === id);
    logActivity("ok", `Job «${job?.name ?? id}» εκτελέστηκε`);
  },
  removeJob(id: ID) {
    set((s) => ({ ...s, jobs: s.jobs.filter((j) => j.id !== id) }));
  },

  // Backups
  runBackup() {
    set((s) => ({
      ...s,
      backups: [
        { id: uid(), at: Date.now(), size: `${44 + Math.floor(Math.random() * 8)} MB`, kind: "manual" },
        ...s.backups,
      ].slice(0, 12),
    }));
    logActivity("ok", "Χειροκίνητο backup ολοκληρώθηκε");
  },

  // Approvals
  resolveApproval(id: ID, status: "approved" | "rejected") {
    const item = state.approvals.find((a) => a.id === id);
    set((s) => ({ ...s, approvals: s.approvals.map((a) => (a.id === id ? { ...a, status } : a)) }));
    if (item && status === "approved") {
      set((s) => ({
        ...s,
        missions: [
          { id: uid(), title: item.title, status: "queued", progress: 0, log: ["Εγκρίθηκε από τον χρήστη"], createdAt: Date.now() },
          ...s.missions,
        ],
      }));
    }
    logActivity(status === "approved" ? "ok" : "warn", `Πρόταση ${status === "approved" ? "εγκρίθηκε" : "απορρίφθηκε"}`);
  },

  // Modules (system/automation sections)
  toggleModule(id: string) {
    set((s) => ({
      ...s,
      modules: { ...s.modules, [id]: { ...(s.modules[id] ?? { enabled: false, runs: 0, lastRun: null }), enabled: !(s.modules[id]?.enabled ?? false) } },
    }));
  },
  runModule(id: string, label: string) {
    set((s) => {
      const m = s.modules[id] ?? { enabled: true, runs: 0, lastRun: null };
      return { ...s, modules: { ...s.modules, [id]: { ...m, runs: m.runs + 1, lastRun: Date.now() } } };
    });
    logActivity("ok", `${label}: εκτέλεση #${(state.modules[id]?.runs ?? 0)}`);
  },

  // Settings
  updateSettings(patch: Partial<Settings>) {
    set((s) => ({ ...s, settings: { ...s.settings, ...patch } }));
  },

  resetAll() {
    set(() => initialState());
    logActivity("warn", "Επαναφορά όλων των δεδομένων");
  },
};
