type Tone = "ok" | "warn" | "muted";

const dot: Record<Tone, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  muted: "bg-muted-foreground/50",
};

function Row({ label, value, tone }: { label: string; value: string; tone: Tone }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/60 py-2 text-sm last:border-0">
      <span className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${dot[tone]}`} aria-hidden />
        {label}
      </span>
      <span className="text-right text-xs text-muted-foreground">{value}</span>
    </div>
  );
}

export function HealthPanel({
  renderStatus,
  renderState,
  checkedAt,
  geminiState,
  geminiMessage,
  missionsLive,
  canTestGemini,
  onRefresh,
  onTestGemini,
}: {
  renderStatus: string | undefined;
  renderState: "loading" | "ready" | "error";
  checkedAt: string | null;
  geminiState: "idle" | "testing" | "ok" | "error";
  geminiMessage: string;
  missionsLive: boolean;
  canTestGemini: boolean;
  onRefresh: () => void;
  onTestGemini: () => void;
}) {
  const renderOk = renderStatus === "ok" || renderStatus === "online" || renderStatus === "healthy";
  const renderTone: Tone = renderState === "loading" ? "muted" : renderOk ? "ok" : "warn";
  const renderValue =
    renderState === "loading" ? "Έλεγχος…" : renderOk ? "Συνδεδεμένο" : "Δεν απαντά";
  const geminiTone: Tone = geminiState === "ok" ? "ok" : geminiState === "error" ? "warn" : "muted";
  const geminiValue =
    geminiState === "ok"
      ? "Απαντά"
      : geminiState === "error"
        ? "Σφάλμα"
        : geminiState === "testing"
          ? "Έλεγχος…"
          : "Δεν ελέγχθηκε";

  return (
    <div>
      <Row label="Render (Nous)" value={renderValue} tone={renderTone} />
      <Row label="Gemini" value={geminiValue} tone={geminiTone} />
      <Row
        label="Live missions"
        value={missionsLive ? "Ενημερώνεται" : "Σε παύση"}
        tone={missionsLive ? "ok" : "muted"}
      />
      {geminiMessage && (
        <p className={`mt-2 text-xs ${geminiState === "ok" ? "text-ok" : "text-warn"}`}>
          {geminiMessage}
        </p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-md border border-border px-3 py-1.5 text-xs"
        >
          Ανανέωση
        </button>
        <button
          type="button"
          onClick={onTestGemini}
          disabled={!canTestGemini || geminiState === "testing"}
          className="rounded-md border border-border px-3 py-1.5 text-xs disabled:opacity-50"
        >
          Έλεγχος Gemini
        </button>
        {checkedAt && (
          <span className="text-[11px] text-muted-foreground">
            Τελευταίος έλεγχος: {new Date(checkedAt).toLocaleTimeString("el-GR")}
          </span>
        )}
      </div>
    </div>
  );
}
