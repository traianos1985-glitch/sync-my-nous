import { ChatMarkdown } from "@/components/nous/chat-markdown";

import { ApprovalList } from "@/components/nous/approval-list";

import {
  Activity,
  ArrowUpRight,
  Loader2,
  Mic,
  MicOff,
  ThumbsDown,
  ThumbsUp,
  Volume2,
  VolumeX,
  RotateCcw,
  Send,
  ShieldAlert,
  Sparkles,
  Square,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Metric } from "./dashboard-primitives";
import type { useDashboard } from "./use-dashboard";

export function DashboardChat({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const {
    section,
    messages,
    draft,
    setDraft,
    isThinking,
    isListening,
    voiceEnabled,
    setVoiceEnabled,
    voiceSupported,
    voiceLanguage,
    setVoiceLanguage,
    pushToTalk,
    setPushToTalk,
    conversationId,
    thinkingSlow,
    chatEndRef,
    chatInputRef,
    stopListening,
    startListening,
    toggleListening,
    researchMode,
    setResearchMode,
    connectionMode,
    activeFocus,
    setActiveFocus,
    approvals,
    approvalStatus,
    systemStatus,
    hasToken,
    geminiTestState,
    geminiTestMessage,
    systemStatusState,
    systemStatusCheckedAt,
    systemStatusError,
    liveMissions,
    liveStatus,
    jobHistory,
    jobHistoryStatus,
    auditEvents,
    auditStatus,
    auditFilter,
    setAuditFilter,
    evaluationMetrics,
    evaluationStatus,
    loadEvaluationMetrics,
    exportEvaluation,
    connectMissionStream,
    loadAuditEvents,
    exportAudit,
    loadJobHistory,
    updateJob,
    loadSystemStatus,
    copyDiagnostics,
    loadApprovals,
    resolveApproval,
    send,
    stopChat,
    focusChatWithPrompt,
    clearChat,
    commandSignals,
    submitFeedback,
    go,
  } = dashboard;
  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col">
      <div className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
        <div className="mx-auto max-w-4xl">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-primary">
                <span className="size-1.5 rounded-full bg-primary shadow-[0_0_14px_var(--primary)]" />
                Agent online · Owner workspace
              </div>
              <h1 className="font-display text-2xl font-semibold tracking-normal sm:text-3xl">
                Τι αναλαμβάνουμε σήμερα;
              </h1>
              <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                Στόχοι, missions, browser operator και κώδικας — σε μία ενιαία ροή με έγκριση πριν
                από κάθε εξωτερική ενέργεια.
              </p>
            </div>
            <div className="hidden rounded-xl border border-border/70 bg-background/50 p-3 text-right sm:block">
              <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                Runtime
              </p>
              <p
                className={`mt-1 text-sm font-semibold ${systemStatus?.status === "degraded" || systemStatus?.status === "unavailable" ? "text-warn" : "text-ok"}`}
              >
                {systemStatus?.status ?? "checking"}
              </p>
            </div>
          </div>
          <section
            className="mb-5 rounded-2xl border border-primary/25 bg-card/70 p-4 "
            aria-labelledby="connection-center-title"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <Activity className="size-4 text-primary" />
                  <h2 id="connection-center-title" className="text-sm font-semibold">
                    Connection Center
                  </h2>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Ξεχωριστός έλεγχος Browser, Render API και Gemini.
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void loadSystemStatus()}
                  className="rounded-lg border border-border px-2.5 py-1.5 text-xs hover:border-primary"
                >
                  Test connection
                </Button>
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void copyDiagnostics()}
                  className="rounded-lg border border-border px-2.5 py-1.5 text-xs hover:border-primary"
                >
                  Copy diagnostic
                </Button>
              </div>
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-3">
              {[
                {
                  label: "Browser",
                  state: "connected",
                  tone: "text-ok",
                  detail: "Το workspace φορτώθηκε",
                },
                {
                  label: "Render API",
                  state:
                    systemStatusState === "loading"
                      ? "waking"
                      : systemStatus?.status === "degraded" ||
                          systemStatus?.status === "unavailable"
                        ? "unavailable"
                        : hasToken
                          ? "connected"
                          : "invalid token",
                  tone:
                    systemStatus?.status === "degraded" || systemStatus?.status === "unavailable"
                      ? "text-warn"
                      : hasToken
                        ? "text-ok"
                        : "text-warn",
                  detail: systemStatusError ?? "Authenticated backend",
                },
                {
                  label: "Gemini",
                  state:
                    geminiTestState === "testing"
                      ? "testing"
                      : geminiTestState === "ok"
                        ? "connected"
                        : geminiTestState === "error"
                          ? "error"
                          : "not tested",
                  tone:
                    geminiTestState === "ok"
                      ? "text-ok"
                      : geminiTestState === "error"
                        ? "text-warn"
                        : "text-muted-foreground",
                  detail: geminiTestMessage || "Πάτησε test για επιβεβαίωση provider",
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-border/70 bg-background/40 p-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium">{item.label}</span>
                    <span
                      className={`flex items-center gap-1.5 font-mono text-[10px] uppercase ${item.tone}`}
                    >
                      <span className="size-1.5 rounded-full bg-current" />
                      {item.state}
                    </span>
                  </div>
                  <p
                    className="mt-2 truncate text-[10px] text-muted-foreground"
                    title={item.detail}
                  >
                    {item.detail}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[10px] text-muted-foreground">
              Τελευταίος έλεγχος:{" "}
              {systemStatusCheckedAt
                ? new Date(systemStatusCheckedAt).toLocaleString("el-GR")
                : "δεν έχει γίνει"}
            </p>
          </section>
          <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {commandSignals.map(({ icon: Icon, label, value, detail, tone }) => (
              <Button
                variant="ghost"
                key={label}
                type="button"
                onClick={() => {
                  const focus = label.toLowerCase();
                  if (focus === "brain") return go("brain");
                  if (focus === "memory") return go("documents");
                  setActiveFocus((current) => (current === focus ? "chat" : focus));
                  if (focus === "guard") void loadApprovals();
                  if (focus === "system") void loadSystemStatus();
                  if (focus === "missions") void connectMissionStream();
                  if (focus === "jobs") void loadJobHistory();
                  if (focus === "audit") void loadAuditEvents();
                  if (focus === "evaluation") void loadEvaluationMetrics();
                }}
                className={`group block h-auto min-h-24 min-w-0 whitespace-normal rounded-lg border p-3 text-left transition-colors ${activeFocus === label.toLowerCase() ? "border-primary/60 bg-primary/10" : "border-border/70 bg-card/60 hover:border-primary/40"}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
                    {label}
                  </span>
                  <Icon className={`size-3.5 ${tone}`} />
                </div>
                <p className={`mt-2 font-display text-lg font-semibold ${tone}`}>{value}</p>
                <p className="mt-0.5 truncate text-[10px] text-muted-foreground">{detail}</p>
              </Button>
            ))}
          </div>
          {activeFocus === "evaluation" && (
            <div className="mb-5 rounded-2xl border border-violet/30 bg-violet/5 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold">Response quality</p>
                  <p className="text-xs text-muted-foreground">
                    Μετρικές από τις αξιολογήσεις των απαντήσεων του NOUS.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    type="button"
                    onClick={() => void loadEvaluationMetrics()}
                    className="rounded-md border border-border px-2.5 py-1.5 text-xs hover:border-primary"
                  >
                    {evaluationStatus === "loading" ? "Φόρτωση…" : "Ανανέωση"}
                  </Button>
                  <Button
                    variant="ghost"
                    type="button"
                    onClick={exportEvaluation}
                    disabled={!evaluationMetrics}
                    className="rounded-md border border-border px-2.5 py-1.5 text-xs hover:border-primary disabled:opacity-40"
                  >
                    Export CSV
                  </Button>
                </div>
              </div>
              {evaluationStatus === "error" ? (
                <p className="mt-4 text-xs text-destructive">Οι μετρικές δεν είναι διαθέσιμες.</p>
              ) : evaluationMetrics ? (
                <>
                  <div className="mt-4 grid grid-cols-3 gap-2">
                    <Metric
                      label="Satisfaction"
                      value={
                        evaluationMetrics.satisfactionRate === null
                          ? "—"
                          : `${Math.round(evaluationMetrics.satisfactionRate * 100)}%`
                      }
                    />
                    <Metric label="Positive" value={String(evaluationMetrics.positive)} />
                    <Metric label="Rated" value={String(evaluationMetrics.total)} />
                  </div>
                  {evaluationMetrics.trend.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <div className="flex items-end gap-1" aria-label="Evaluation trend">
                        {evaluationMetrics.trend.slice(-14).map((point) => {
                          const total = point.positive + point.negative;
                          const positiveRatio = total ? point.positive / total : 0;
                          return (
                            <div
                              key={point.day}
                              className="flex min-w-0 flex-1 flex-col items-center gap-1"
                              title={`${point.day}: ${point.positive} positive, ${point.negative} negative`}
                            >
                              <div className="flex h-16 w-full items-end gap-0.5 rounded-sm bg-muted/30 p-0.5">
                                <div
                                  className="w-1/2 rounded-t-sm bg-ok/70"
                                  style={{
                                    height: `${Math.max(positiveRatio * 100, total ? 8 : 0)}%`,
                                  }}
                                />
                                <div
                                  className="w-1/2 rounded-t-sm bg-destructive/70"
                                  style={{
                                    height: `${Math.max((1 - positiveRatio) * 100, total ? 8 : 0)}%`,
                                  }}
                                />
                              </div>
                              <span className="truncate text-[8px] text-muted-foreground">
                                {point.day.slice(5)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                      <p className="text-[10px] text-muted-foreground">
                        Τάση αξιολογήσεων τελευταίων 14 ημερών
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <p className="mt-4 text-xs text-muted-foreground">
                  Πάτησε «Ανανέωση�� για να φορτώσεις τα metrics.
                </p>
              )}
            </div>
          )}
          {activeFocus === "audit" && (
            <div className="mb-5 rounded-2xl border border-signal/30 bg-signal/5 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-semibold">Audit timeline</p>
                  <p className="text-xs text-muted-foreground">
                    Ιστορικό ενεργειών και approvals των τελευταίων 30 ημερών.
                  </p>
                  <input
                    value={auditFilter}
                    onChange={(event) => setAuditFilter(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") void loadAuditEvents();
                    }}
                    placeholder="Filter event…"
                    aria-label="Φίλτρο audit event"
                    className="mt-2 w-full rounded-md border border-border bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    type="button"
                    onClick={() => void loadAuditEvents()}
                    className="rounded-lg border border-signal/30 px-3 py-1.5 text-xs text-signal"
                  >
                    {auditStatus === "loading" ? "Φόρτωση…" : "Ανανέωση"}
                  </Button>
                  <Button
                    variant="ghost"
                    type="button"
                    onClick={() => void exportAudit()}
                    className="rounded-lg border border-border px-3 py-1.5 text-xs"
                  >
                    Export CSV
                  </Button>
                </div>
              </div>
              {auditStatus === "error" ? (
                <p className="mt-4 text-xs text-destructive">
                  Δεν ήταν δυνατή η φόρτωση του audit timeline.
                </p>
              ) : auditEvents.length === 0 ? (
                <p className="mt-4 text-xs text-muted-foreground">
                  Δεν υπάρχουν audit events ακόμη.
                </p>
              ) : (
                <div className="mt-3 max-h-64 space-y-2 overflow-auto pr-1">
                  {auditEvents.map((event) => (
                    <div
                      key={event.id}
                      className="flex items-center justify-between gap-3 rounded-lg bg-card/70 p-2.5 text-xs"
                    >
                      <span className="font-medium">{event.event}</span>
                      <time className="text-[10px] text-muted-foreground">
                        {new Date(event.createdAt).toLocaleString()}
                      </time>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {activeFocus === "jobs" && (
            <div className="mb-5 rounded-2xl border border-primary/30 bg-primary/5 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold">Job control center</p>
                  <p className="text-xs text-muted-foreground">
                    Ιστορικό, retries και ασφαλές cancellation.
                  </p>
                </div>
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void loadJobHistory()}
                  className="rounded-lg border border-primary/30 px-3 py-1.5 text-xs text-primary"
                >
                  {jobHistoryStatus === "loading" ? "Φόρτωση…" : "Ανανέωση"}
                </Button>
              </div>
              {jobHistoryStatus === "error" ? (
                <p className="mt-4 text-xs text-destructive">
                  Δεν ήταν δυνατή η φόρτωση του job history.
                </p>
              ) : jobHistory.length === 0 ? (
                <p className="mt-4 text-xs text-muted-foreground">Δεν υπάρχουν jobs ακόμη.</p>
              ) : (
                <div className="mt-3 space-y-2">
                  {jobHistory.map((job) => (
                    <div key={job.id} className="rounded-lg bg-card/70 p-3">
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="font-medium">{job.kind}</span>
                        <span className="font-mono text-muted-foreground">{job.status}</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between gap-3 text-[10px] text-muted-foreground">
                        <span>retries: {job.retryCount}</span>
                        <div className="flex gap-2">
                          {["queued", "running"].includes(job.status) && (
                            <Button
                              variant="ghost"
                              type="button"
                              onClick={() => void updateJob(job.id, "cancel")}
                              className="text-destructive hover:underline"
                            >
                              Cancel
                            </Button>
                          )}
                          {job.status === "failed" && job.retryCount < 3 && (
                            <Button
                              variant="ghost"
                              type="button"
                              onClick={() => void updateJob(job.id, "retry")}
                              className="text-primary hover:underline"
                            >
                              Retry
                            </Button>
                          )}
                        </div>
                      </div>
                      {job.lastError && (
                        <p className="mt-2 truncate text-[10px] text-destructive">
                          {job.lastError}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {activeFocus === "missions" && (
            <div className="mb-5 rounded-2xl border border-primary/30 bg-primary/5 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold">Live mission progress</p>
                  <p className="text-xs text-muted-foreground">
                    Ανανέωση από το Render backend κάθε 3 δευτερόλεπτα.
                  </p>
                </div>
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void connectMissionStream()}
                  className="rounded-lg border border-primary/30 px-3 py-1.5 text-xs text-primary"
                >
                  {liveStatus === "connected" ? "Live" : "Σύνδεση"}
                </Button>
              </div>
              <div className="mt-3 space-y-2">
                {liveMissions.length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    Δεν υπάρχουν missions ή δεν έχε�� συνδεθεί ακόμη το live stream.
                  </p>
                )}
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
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void loadSystemStatus()}
                  className="rounded-lg border border-signal/30 px-3 py-1.5 text-xs text-signal hover:bg-signal/10"
                >
                  Ανανέωση
                </Button>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-lg bg-card/70 p-2">
                  <p className="text-muted-foreground">Status</p>
                  <p className="mt-1 font-semibold text-ok">{systemStatus?.status ?? "loading"}</p>
                </div>
                <div className="rounded-lg bg-card/70 p-2">
                  <p className="text-muted-foreground">Missions</p>
                  <p className="mt-1 font-semibold">{systemStatus?.counts?.missions ?? "—"}</p>
                </div>
                <div className="rounded-lg bg-card/70 p-2">
                  <p className="text-muted-foreground">Tool runs</p>
                  <p className="mt-1 font-semibold">{systemStatus?.counts?.toolRuns ?? "—"}</p>
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
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void loadApprovals()}
                  className="rounded-lg border border-warn/30 px-3 py-1.5 text-xs text-warn hover:bg-warn/10"
                >
                  {approvalStatus === "loading" ? "Έλεγχος…" : "Ανανέωση"}
                </Button>
              </div>
              <div className="mt-3">
                <ApprovalList
                  approvals={approvals}
                  status={approvalStatus}
                  onResolve={resolveApproval}
                />
              </div>
            </div>
          )}
          <section
            className="mb-5 rounded-2xl border border-primary/25 bg-primary/5 p-4"
            aria-labelledby="control-center-title"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
                  Unified control center
                </p>
                <h2 id="control-center-title" className="mt-1 text-sm font-semibold">
                  Ένα chat για όλο το NOUS
                </h2>
                <p className="mt-1 max-w-2xl text-xs text-muted-foreground">
                  Ζήτησε έλεγχο, διάγνωση ή ενέργεια από εδώ. Ο agent θα χρησιμοποιήσει τα
                  συνδεδεμένα εργαλεία και θα ζητήσει έγκριση πριν από εξωτερική αλλαγή.
                </p>
              </div>
              <span className="rounded-full border border-ok/30 bg-ok/10 px-2 py-1 font-mono text-[10px] text-ok">
                approval-first
              </span>
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  icon: Sparkles,
                  label: "Πλήρης έλεγχος",
                  prompt:
                    "Κάνε πλήρη έλεγχο του NOUS: υγεία, missions, jobs, μνήμη, approvals και διαθέσιμα εργαλεία. Δώσε μου προτεραιότητες και επόμενα βήματα.",
                },
                {
                  icon: Activity,
                  label: "Τρέχουσα εργασία",
                  prompt:
                    "Δείξε μου όλα τα ενεργά missions και jobs, τι έχει κολλήσει και ποια ενέργεια προτείνεις.",
                },
                {
                  icon: ShieldAlert,
                  label: "Διάγνωση",
                  prompt:
                    "Κάνε ασφαλή διάγνωση για προβλήματα στο backend, στις συνδέσεις και στα εργαλεία. Μην αλλάξεις τίποτα χωρίς έγκριση.",
                },
                {
                  icon: ArrowUpRight,
                  label: "Σχέδιο αναβάθμισης",
                  prompt:
                    "Ανάλυσε τι μπορεί να αναβαθμιστεί ουσιαστικά στο NOUS με βάση τις δυνατότητες και τα διαθέσιμα εργαλεία. Ταξινόμησε impact, ρίσκο και effort.",
                },
              ].map(({ icon: Icon, label, prompt }) => (
                <Button
                  variant="ghost"
                  key={label}
                  type="button"
                  onClick={() => focusChatWithPrompt(prompt)}
                  disabled={isThinking}
                  className="group flex items-center gap-2 rounded-xl border border-border/70 bg-card/60 px-3 py-2.5 text-left text-xs transition-colors hover:border-primary/50 hover:bg-primary/8 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Icon className="size-3.5 text-primary transition-transform group-hover:scale-110" />
                  <span>{label}</span>
                </Button>
              ))}
            </div>
          </section>
          <div className="flex flex-col gap-3">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`min-w-0 max-w-full rounded-2xl border p-4 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "self-end whitespace-pre-wrap border-border bg-violet/15"
                    : m.error
                      ? "border-destructive/40 bg-destructive/5 text-destructive"
                      : "border-border bg-card/80"
                }`}
              >
                {m.role === "user" ? m.text : <ChatMarkdown text={m.text} />}
                {m.error && m.retryText && (
                  <Button
                    variant="ghost"
                    type="button"
                    onClick={() => void send(m.retryText, { retry: true })}
                    disabled={isThinking}
                    className="mt-3 inline-flex items-center gap-1 rounded-lg border border-destructive/40 px-3 py-1.5 text-xs font-semibold text-destructive hover:bg-destructive/10 disabled:opacity-50"
                  >
                    <RotateCcw className="size-3" /> Ξαναδοκίμασε
                  </Button>
                )}
                {m.role === "assistant" && m.id !== "welcome" && !m.error && (
                  <div className="mt-3 flex items-center gap-1 border-t border-border/60 pt-2">
                    <span className="mr-2 text-[10px] text-muted-foreground">
                      Αξιολόγηση απάντησης
                    </span>
                    <Button
                      variant="ghost"
                      type="button"
                      onClick={() => void submitFeedback(m.id, "positive")}
                      aria-label="Χρήσιμη απάντηση"
                      className={`rounded-md p-1.5 transition-colors ${m.feedback === "positive" ? "bg-ok/15 text-ok" : "text-muted-foreground hover:bg-ok/10 hover:text-ok"}`}
                    >
                      <ThumbsUp className="size-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      type="button"
                      onClick={() => void submitFeedback(m.id, "negative")}
                      aria-label="Μη χρήσιμη απάντηση"
                      className={`rounded-md p-1.5 transition-colors ${m.feedback === "negative" ? "bg-destructive/15 text-destructive" : "text-muted-foreground hover:bg-destructive/10 hover:text-destructive"}`}
                    >
                      <ThumbsDown className="size-3.5" />
                    </Button>
                  </div>
                )}
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
            {isThinking && (
              <div
                role="status"
                className="flex items-center gap-2 rounded-2xl border border-border bg-card/60 p-4 text-sm text-muted-foreground"
              >
                <Loader2 className="size-4 animate-spin text-primary" />
                {thinkingSlow
                  ? "Ακόμη δουλεύω… Αν το Render ξυπνά από cold start, μπορεί να πάρει έως ένα λεπτό."
                  : researchMode === "deep"
                    ? "Αναζήτηση → σύνθεση…"
                    : "Ο ΝΟΥΣ σκέφτεται…"}
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>
      </div>
      <div className="min-w-0 border-t border-border/70 bg-card/75 p-4 backdrop-blur-xl">
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
                onChange={(event) => setResearchMode(event.target.value as "auto" | "off" | "deep")}
                disabled={isThinking}
                className="bg-transparent text-[10px] outline-none disabled:opacity-50"
              >
                <option value="auto">Research: Auto</option>
                <option value="deep">Research: Deep</option>
                <option value="off">Research: Off</option>
              </select>
            </label>
          </div>
          <Button
            variant="ghost"
            type="button"
            onClick={clearChat}
            disabled={messages.length <= 1 && !conversationId}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Καθαρισμός συνομιλίας"
          >
            <RotateCcw className="size-3" /> Καθαρισμός
          </Button>
        </div>
        <div className="mx-auto mb-2 flex max-w-3xl flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <label className="flex items-center gap-2">
            <span>Γλώσσα φωνής</span>
            <select
              value={voiceLanguage}
              onChange={(event) => setVoiceLanguage(event.target.value)}
              className="rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground"
            >
              <option value="el-GR">Ελληνικά</option>
              <option value="en-US">English</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={pushToTalk}
              onChange={(event) => {
                stopListening();
                setPushToTalk(event.target.checked);
              }}
              disabled={!voiceSupported}
            />
            Push-to-talk
          </label>
        </div>
        <div className="mx-auto flex min-w-0 max-w-3xl gap-2">
          <Button
            variant="ghost"
            type="button"
            onClick={pushToTalk ? undefined : toggleListening}
            onPointerDown={pushToTalk ? startListening : undefined}
            onPointerUp={pushToTalk ? stopListening : undefined}
            onPointerLeave={pushToTalk && isListening ? stopListening : undefined}
            disabled={!voiceSupported || isThinking}
            aria-label={
              pushToTalk
                ? "Κράτα πατημένο για να μιλήσεις"
                : isListening
                  ? "Σταμάτησε την ακρόαση"
                  : "Μίλησε στον ΝΟΥΣ"
            }
            title={
              !voiceSupported
                ? "Η φωνητική εισαγωγή δεν υποστηρίζεται σε αυτόν τον browser"
                : pushToTalk
                  ? "Κράτα πατημένο, μίλα και άφησε για αποστολή"
                  : undefined
            }
            className={`inline-flex size-11 shrink-0 items-center justify-center rounded-xl border transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${isListening ? "border-destructive/60 bg-destructive/15 text-destructive" : "border-border bg-background text-muted-foreground hover:border-primary hover:text-primary"}`}
          >
            {isListening ? <MicOff className="size-4" /> : <Mic className="size-4" />}
          </Button>
          <textarea
            ref={chatInputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            aria-label="Μήνυμα προς τον NOUS"
            aria-describedby="chat-input-hint"

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
            className="min-w-0 flex-1 resize-none rounded-xl border border-input bg-background p-3 text-sm outline-none focus:border-primary"
          />
          <Button
            variant="ghost"
            type="button"
            onClick={() => {
              setVoiceEnabled((enabled) => {
                if (enabled) window.speechSynthesis?.cancel();
                return !enabled;
              });
            }}
            disabled={!voiceSupported}
            aria-label={voiceEnabled ? "Σίγασε τη φωνή του ΝΟΥΣ" : "Ενεργοποίησε τη φωνή του ΝΟΥΣ"}
            className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl border border-border bg-background text-muted-foreground hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"
          >
            {voiceEnabled ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
          </Button>
          {isThinking ? (
            <Button
              variant="ghost"
              type="button"
              onClick={stopChat}
              className="inline-flex items-center gap-2 rounded-xl border border-destructive/50 bg-destructive/10 px-4 text-sm font-semibold text-destructive"
              aria-label="Διακοπή απάντησης"
            >
              <Square className="size-4" />
              <span className="hidden sm:inline">Διακοπή</span>
            </Button>
          ) : (
            <Button
              variant="ghost"
              type="button"
              onClick={() => void send()}
              disabled={!draft.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Στείλε μήνυμα"
            >
              <Send className="size-4" />
              <span className="hidden sm:inline">Στείλε</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
