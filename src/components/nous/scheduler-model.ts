export type StorageReport = {
  ok: boolean;
  mode: "persistent_disk" | "declared_persistent" | "ephemeral" | "local_disk" | string;
  durable: boolean;
  host?: string;
  autonomy_enabled_by_default?: boolean;
  warning?: string | null;
};

export type ExternalTickResult = {
  ok: boolean;
  ran: boolean;
  reason?: string;
  next_due_in?: number;
  loop_running?: boolean;
};

const STORAGE_LABELS: Record<string, string> = {
  persistent_disk: "Μόνιμος δίσκος",
  declared_persistent: "Μόνιμη αποθήκευση (δηλωμένη)",
  ephemeral: "Προσωρινός δίσκος",
  local_disk: "Τοπικός δίσκος",
};

export function storageLabel(report: StorageReport | null): string {
  if (!report) return "Άγνωστο";
  return STORAGE_LABELS[report.mode] ?? report.mode;
}

/** URL an external scheduler (e.g. cron-job.org) should POST to. */
export function schedulerCycleUrl(apiBase: string): string {
  return `${apiBase.replace(/\/+$/, "")}/remote/service/cycle`;
}

const TICK_REASONS: Record<string, string> = {
  ran: "Εκτελέστηκε ένας κύκλος.",
  not_due: "Δεν ήταν ώρα για νέο κύκλο.",
  disabled: "Η αυτονομία είναι απενεργοποιημένη.",
  emergency_stop: "Ενεργό Emergency Stop.",
  cycle_already_running: "Ήδη τρέχει κύκλος.",
};

export function describeTick(result: ExternalTickResult): string {
  const base = TICK_REASONS[result.reason ?? ""] ?? result.reason ?? "Άγνωστο αποτέλεσμα.";
  if (result.reason === "not_due" && typeof result.next_due_in === "number") {
    return `${base} Επόμενος σε ${Math.ceil(result.next_due_in)}s.`;
  }
  return base;
}
