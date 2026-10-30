export type AutonomyServiceState = {
  enabled: boolean | null;
  interval: number;
  last_heartbeat: number | null;
  last_run: number | null;
  last_error: string | null;
  cycles: number;
  emergency_stop?: boolean;
  battery?: { status?: string; level?: number; ok?: boolean } | null;
  status: "healthy" | "degraded" | string;
  log_file?: string;
  error?: string;
};

export type WatchdogStatus = {
  ok: boolean;
  enabled: boolean | null;
  action: "none" | "needs_attention" | "needs_restart" | string;
  reason?: string;
  silence?: number;
};

export type AutonomyEventItem = {
  time: number;
  event: string;
  data?: Record<string, unknown>;
};

export const MIN_INTERVAL_SECONDS = 5;
export const MAX_INTERVAL_SECONDS = 86400;
export const DEFAULT_INTERVAL_SECONDS = 300;

export const INTERVAL_PRESETS = [
  { label: "30δ", value: 30 },
  { label: "1λ", value: 60 },
  { label: "5λ", value: 300 },
  { label: "10λ", value: 600 },
  { label: "30λ", value: 1800 },
];

export function validateInterval(raw: number | string): {
  valid: boolean;
  value: number;
  error?: string;
} {
  const parsed = typeof raw === "number" ? Math.floor(raw) : parseInt(String(raw).trim(), 10);
  if (Number.isNaN(parsed)) {
    return {
      valid: false,
      value: DEFAULT_INTERVAL_SECONDS,
      error: "Το διάστημα πρέπει να είναι έγκυρος ακέραιος αριθμός δευτερολέπτων.",
    };
  }
  if (parsed < MIN_INTERVAL_SECONDS) {
    return {
      valid: false,
      value: parsed,
      error: `Το ελάχιστο διάστημα εκτέλεσης είναι ${MIN_INTERVAL_SECONDS} δευτερόλεπτα.`,
    };
  }
  if (parsed > MAX_INTERVAL_SECONDS) {
    return {
      valid: false,
      value: parsed,
      error: `Το μέγιστο διάστημα εκτέλεσης είναι ${MAX_INTERVAL_SECONDS} δευτερόλεπτα (24 ώρες).`,
    };
  }
  return { valid: true, value: parsed };
}

export function formatElapsedSeconds(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds) || seconds < 0) {
    return "ποτέ";
  }
  const s = Math.floor(seconds);
  if (s < 1) return "μόλις τώρα";
  if (s < 60) return `${s}δ πριν`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}λ πριν`;
  const h = Math.floor(m / 60);
  const remainingM = m % 60;
  return `${h}ω ${remainingM}λ πριν`;
}

export function formatEventTimestamp(timestamp: number): string {
  if (!timestamp || Number.isNaN(timestamp)) return "—";
  try {
    const d = new Date(timestamp * 1000);
    return d.toLocaleTimeString("el-GR", { hour12: false });
  } catch {
    return "—";
  }
}

export type EventBadgeInfo = {
  label: string;
  tone: "ok" | "warn" | "destructive" | "info" | "muted";
};

export function formatEventBadge(event: string): EventBadgeInfo {
  switch (event) {
    case "service_cycle_ok":
      return { label: "Επιτυχής κύκλος", tone: "ok" };
    case "service_cycle_error":
      return { label: "Σφάλμα κύκλου", tone: "destructive" };
    case "emergency_stop":
      return { label: "Emergency Stop", tone: "destructive" };
    case "service_enabled":
      return { label: "Ενεργοποίηση", tone: "info" };
    case "service_disabled":
      return { label: "Παύση", tone: "warn" };
    case "watchdog_warning":
      return { label: "Προειδοποίηση Watchdog", tone: "warn" };
    case "service_skip":
      return { label: "Παράλειψη", tone: "muted" };
    case "service_loop_started":
      return { label: "Εκκίνηση loop", tone: "info" };
    case "service_loop_stopped":
      return { label: "Τερματισμός loop", tone: "warn" };
    default:
      return { label: event, tone: "muted" };
  }
}

export function isEmergencyStopped(state: AutonomyServiceState | null | undefined): boolean {
  return Boolean(state?.emergency_stop);
}

export function getWatchdogTone(
  watchdog: WatchdogStatus | null | undefined,
): "ok" | "warn" | "destructive" | "muted" {
  if (!watchdog) return "muted";
  if (!watchdog.ok) {
    return watchdog.action === "needs_restart" ? "destructive" : "warn";
  }
  return "ok";
}

export function filterAutonomyEvents(
  events: AutonomyEventItem[],
  filterType: string,
  query: string,
): AutonomyEventItem[] {
  const q = query.trim().toLowerCase();
  return events.filter((ev) => {
    if (filterType === "errors") {
      if (ev.event !== "service_cycle_error" && ev.event !== "emergency_stop") return false;
    } else if (filterType === "cycles") {
      if (ev.event !== "service_cycle_ok" && ev.event !== "service_cycle_error") return false;
    } else if (filterType === "lifecycle") {
      if (
        ev.event !== "service_enabled" &&
        ev.event !== "service_disabled" &&
        ev.event !== "emergency_stop"
      ) {
        return false;
      }
    }

    if (!q) return true;
    if (ev.event.toLowerCase().includes(q)) return true;
    if (ev.data && JSON.stringify(ev.data).toLowerCase().includes(q)) return true;
    return false;
  });
}
