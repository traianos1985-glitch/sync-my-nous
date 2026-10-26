export type MissionTone = "ok" | "warn" | "danger" | "active" | "muted";

export type MissionStatusMeta = { label: string; tone: MissionTone; active: boolean };

// One place that maps every status the Render backend or the web DB can report
// to a Greek label and a colour tone, so the home card and the Missions page agree.
const statusMap: Record<string, MissionStatusMeta> = {
  queued: { label: "Σε αναμονή", tone: "muted", active: true },
  pending: { label: "Σε αναμονή", tone: "muted", active: true },
  planning: { label: "Σχεδιάζεται", tone: "active", active: true },
  awaiting_approval: { label: "Θέλει έγκριση", tone: "warn", active: true },
  running: { label: "Εκτελείται", tone: "active", active: true },
  in_progress: { label: "Εκτελείται", tone: "active", active: true },
  completed: { label: "Ολοκληρώθηκε", tone: "ok", active: false },
  done: { label: "Ολοκληρώθηκε", tone: "ok", active: false },
  success: { label: "Ολοκληρώθηκε", tone: "ok", active: false },
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
