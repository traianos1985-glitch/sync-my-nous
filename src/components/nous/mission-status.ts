export type MissionTone = "ok" | "warn" | "danger" | "active" | "muted";

export type MissionStatusMeta = { label: string; tone: MissionTone; active: boolean };

// One place that maps every status the Render backend or the web DB can report
// to a Greek label and a colour tone, so the home card and the Missions page agree.
const statusMap: Record<string, MissionStatusMeta> = {
  queued: { label: "Σε αναμονή", tone: "muted", active: true },
  pending: { label: "Σε αναμονή", tone: "muted", active: true },
  active: { label: "Σε εξέλιξη", tone: "active", active: true },
  planning: { label: "Σχεδιάζεται", tone: "active", active: true },
  awaiting_approval: { label: "Θέλει έγκριση", tone: "warn", active: true },
  waiting_approval: { label: "Θέλει έγκριση", tone: "warn", active: true },
  blocked: { label: "Μπλοκαρισμένη", tone: "warn", active: false },
  needs_review: { label: "Θέλει έλεγχο", tone: "warn", active: false },
  running: { label: "Εκτελείται", tone: "active", active: true },
  in_progress: { label: "Εκτελείται", tone: "active", active: true },
  completed: { label: "Ολοκληρώθηκε", tone: "ok", active: false },
  done: { label: "Ολοκληρώθηκε", tone: "ok", active: false },
  success: { label: "Ολοκληρώθηκε", tone: "ok", active: false },
  verified: { label: "Επαληθεύτηκε", tone: "ok", active: false },
  failed: { label: "Απέτυχε", tone: "danger", active: false },
  error: { label: "Απέτυχε", tone: "danger", active: false },
  cancelled: { label: "Ακυρώθηκε", tone: "muted", active: false },
  rejected: { label: "Απορρίφθηκε", tone: "muted", active: false },
};

export function missionStatusMeta(status: string | undefined | null): MissionStatusMeta {
  const key = String(status ?? "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
  return statusMap[key] ?? { label: key || "άγνωστο", tone: "muted", active: false };
}

export const missionToneClass: Record<MissionTone, string> = {
  ok: "text-ok bg-ok/10 border-ok/30",
  warn: "text-warn bg-warn/10 border-warn/30",
  danger: "text-destructive bg-destructive/10 border-destructive/30",
  active: "text-primary bg-primary/10 border-primary/30",
  muted: "text-muted-foreground bg-muted/30 border-border",
};

export function summarizeMissions(missions: Array<{ status: string }>) {
  const summary = { active: 0, awaiting: 0, failed: 0, completed: 0 };
  for (const mission of missions) {
    const meta = missionStatusMeta(mission.status);
    if (meta.tone === "warn") summary.awaiting += 1;
    if (meta.tone === "danger") summary.failed += 1;
    if (meta.tone === "ok") summary.completed += 1;
    if (meta.active) summary.active += 1;
  }
  return summary;
}

export type MissionFilterTab = "all" | "active" | "awaiting" | "failed" | "completed";

export function filterMissions<T extends { id: string; title: string; status: string }>(
  missions: T[],
  tab: MissionFilterTab,
  query = "",
): T[] {
  const q = query.trim().toLowerCase();
  return missions.filter((mission) => {
    const meta = missionStatusMeta(mission.status);
    if (tab === "active" && !meta.active) return false;
    if (tab === "awaiting" && meta.tone !== "warn") return false;
    if (tab === "failed" && meta.tone !== "danger") return false;
    if (tab === "completed" && meta.tone !== "ok") return false;
    if (q) {
      const matchTitle = mission.title.toLowerCase().includes(q);
      const matchId = mission.id.toLowerCase().includes(q);
      if (!matchTitle && !matchId) return false;
    }
    return true;
  });
}

export type LiveMission = {
  id: string;
  title: string;
  status: string;
  tasksDone?: number;
  tasksTotal?: number;
  currentStep?: string | null;
  currentStepStatus?: string | null;
};

type RawTask = { title?: unknown; action?: unknown; status?: unknown };
type RawMission = {
  id?: unknown;
  title?: unknown;
  name?: unknown;
  status?: unknown;
  tasks?: unknown;
};

// Finished steps, successful or not. Blocked and needs_review steps stay open.
const finishedTaskStatuses = new Set([
  "done",
  "completed",
  "verified",
  "failed",
  "rejected",
  "cancelled",
]);
// Which step counts as "current": what runs or waits for approval, then what is
// stuck or failed, then the next pending one.
const currentStepOrder = [
  ["running", "waiting_approval"],
  ["blocked", "needs_review", "failed"],
  ["pending"],
];

/** Maps one GET /remote/missions entry to what the mission list shows. */
export function normalizeMission(raw: unknown): LiveMission | null {
  if (!raw || typeof raw !== "object") return null;
  const mission = raw as RawMission;
  if (mission.id === undefined || mission.id === null) return null;
  const tasks = Array.isArray(mission.tasks)
    ? (mission.tasks as unknown[]).filter((t): t is RawTask => Boolean(t && typeof t === "object"))
    : [];
  const taskStatus = (task: RawTask) => String(task.status ?? "pending");
  let current: RawTask | undefined;
  for (const group of currentStepOrder) {
    current = tasks.find((task) => group.includes(taskStatus(task)));
    if (current) break;
  }
  return {
    id: String(mission.id),
    title: String(mission.title ?? mission.name ?? "Untitled mission"),
    status: String(mission.status ?? "unknown"),
    tasksDone: tasks.filter((task) => finishedTaskStatuses.has(taskStatus(task))).length,
    tasksTotal: tasks.length,
    currentStep: current ? String(current.title ?? current.action ?? "βήμα") : null,
    currentStepStatus: current ? taskStatus(current) : null,
  };
}

/**
 * The backend runs only pending steps of active or blocked missions, one at a
 * time, and refuses while a step runs, waits for approval or needs review.
 */
export function canRunNextStep(mission: LiveMission): boolean {
  return (
    (mission.status === "active" || mission.status === "blocked") &&
    mission.currentStepStatus === "pending"
  );
}

export type RunNextOutcome = { ok: boolean; message: string };

type RunNextResponse = {
  ok?: boolean;
  idle?: boolean;
  busy?: boolean;
  blocked?: boolean;
  needs_review?: boolean;
  approval_required?: boolean;
  error?: string;
  mission?: { status?: string };
};

/** Turns a POST /remote/missions/run-next response into a short Greek message. */
export function describeRunNext(response: unknown): RunNextOutcome {
  const r = (response && typeof response === "object" ? response : {}) as RunNextResponse;
  if (r.ok === true) {
    if (r.idle) return { ok: true, message: "Δεν υπάρχει άλλο βήμα για εκτέλεση." };
    return {
      ok: true,
      message:
        r.mission?.status === "done"
          ? "Το τελευταίο βήμα εκτελέστηκε· η αποστολή ολοκληρώθηκε."
          : "Το βήμα εκτελέστηκε.",
    };
  }
  if (r.approval_required) {
    return { ok: false, message: "Το βήμα θέλει έγκριση· δες τις Εγκρίσεις." };
  }
  if (r.busy) return { ok: false, message: "Ήδη εκτελείται ένα βήμα αυτής της αποστολής." };
  if (r.needs_review) {
    return { ok: false, message: "Ένα προηγούμενο βήμα θέλει έλεγχο πριν συνεχίσει." };
  }
  switch (r.error) {
    case "mission_not_found":
      return { ok: false, message: "Η αποστολή δεν βρέθηκε." };
    case "mission_not_active":
      return { ok: false, message: "Η αποστολή δεν είναι ενεργή." };
    case "mission_plan_integrity_failure":
      return { ok: false, message: "Το σχέδιο της αποστολής άλλαξε· μπλοκαρίστηκε για έλεγχο." };
  }
  if (r.blocked) return { ok: false, message: "Η αποστολή μπλοκαρίστηκε σε αυτό το βήμα." };
  return { ok: false, message: "Το βήμα απέτυχε· η αποστολή σταμάτησε για έλεγχο." };
}
