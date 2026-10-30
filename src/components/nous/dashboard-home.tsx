import { SectionPanel } from "@/components/nous/section-panel";
import { MissionList } from "@/components/nous/mission-list";
import { ApprovalList } from "@/components/nous/approval-list";
import { HealthPanel } from "@/components/nous/health-panel";

import { hasConfiguredNousApi } from "@/lib/nous-api";

import { Button } from "@/components/ui/button";
import { Card } from "./dashboard-primitives";
import type { useDashboard } from "./use-dashboard";
import { ConnectionSettings } from "./dashboard-connection-settings";
import { useEffect, useState } from "react";
import { TelemetryPanel } from "./telemetry-panel";
import { CognitiveMemoryPanel } from "./cognitive-memory-panel";
import { MobileBridgePanel } from "./mobile-bridge-panel";
import { appendResourcePoint, type ResourcePoint } from "./telemetry-model";

const snapshotLabels = [
  "Health",
  "API connection",
  "Missions σε εξέλιξη",
  "Tool runs",
  "Storage",
  "CPU",
  "Memory",
  "Overview",
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

export function DashboardHome({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const [resourceHistory, setResourceHistory] = useState<ResourcePoint[]>([]);
  const {
    initiativePending,
    section,
    failedInitiative,
    initiatives,
    initiativesState,
    companionStatus,
    approvals,
    approvalStatus,
    systemStatus,
    hasToken,
    geminiTestState,
    geminiTestMessage,
    systemStatusState,
    systemStatusCheckedAt,
    liveMissions,
    liveStatus,
    missionSummary,
    loadSystemStatus,
    testGeminiConnection,
    resolveApproval,
    loadApprovals,
    loadInitiatives,
    resolveInitiative,
    loadCompanionStatus,
  } = dashboard;

  useEffect(() => {
    if (!systemStatusCheckedAt) return;
    const timer = window.setTimeout(() => {
      setResourceHistory((history) =>
        appendResourcePoint(history, {
          time: new Date(systemStatusCheckedAt).toLocaleTimeString("el-GR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          cpu: systemStatus?.metrics?.cpu_percent ?? null,
          memory: systemStatus?.metrics?.memory_percent ?? null,
        }),
      );
    }, 1);
    return () => window.clearTimeout(timer);
  }, [
    systemStatusCheckedAt,
    systemStatus?.metrics?.cpu_percent,
    systemStatus?.metrics?.memory_percent,
  ]);

  return (
    <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
      <div className="min-w-0 max-w-full rounded-2xl border border-border bg-gradient-to-br from-violet/20 to-primary/10 p-5">
        <h1 className="font-display text-2xl font-bold">Καλώς ήρθες στο�� ΝΟΥΣ</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Agent chat + workspace + Android companion + deploy, σε μία οθόνη.
        </p>
      </div>

      <CognitiveMemoryPanel />
      <MobileBridgePanel />

      <div className="mt-4 grid min-w-0 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Active missions",
            value: systemStatus?.counts?.missions ?? "—",
            detail: liveMissions.length ? "Live stream connected" : "Awaiting live stream",
            tone: "text-violet",
          },
          {
            label: "Pending approvals",
            value: approvals.length,
            detail: approvals.length ? "Needs your decision" : "Queue is clear",
            tone: approvals.length ? "text-warn" : "text-ok",
          },
          {
            label: "Tool runs",
            value: systemStatus?.counts?.toolRuns ?? "—",
            detail: "Recorded in the workspace",
            tone: "text-signal",
          },
          {
            label: "System health",
            value: systemStatus?.status ?? "—",
            detail:
              typeof systemStatus?.overview === "string"
                ? systemStatus.overview
                : "Connect to load status",
            tone:
              systemStatus?.status === "ok" || systemStatus?.status === "online"
                ? "text-ok"
                : "text-muted-foreground",
          },
        ].map((metric) => (
          <div
            key={metric.label}
            className="min-w-0 rounded-2xl border border-border bg-card/70 p-4"
          >
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              {metric.label}
            </p>
            <p className={`mt-2 truncate font-mono text-xl font-semibold ${metric.tone}`}>
              {metric.value}
            </p>
            <p className="mt-1 truncate text-xs text-muted-foreground">{metric.detail}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-2xl border border-border bg-card/70 p-4 md:p-5">
        <TelemetryPanel
          history={resourceHistory}
          cpu={systemStatus?.metrics?.cpu_percent}
          memory={systemStatus?.metrics?.memory_percent}
          uptime={systemStatus?.metrics?.uptime_s}
          checkedAt={systemStatusCheckedAt}
          missions={missionSummary}
          missionCount={systemStatus?.counts?.missions ?? null}
          geminiState={geminiTestState}
        />
      </div>

      <div className="mt-4 grid min-w-0 gap-4 lg:grid-cols-2">
        <Card title="System Snapshot">
          <ConnectionSettings dashboard={dashboard} />
          {systemStatusState === "loading" && (
            <p className="mb-3 text-xs text-muted-foreground">
              Σύνδεση με NOUS API… Το Render μπορεί να ξυπνά από cold start.
            </p>
          )}
          {systemStatusState === "error" && (
            <p className="mb-3 text-xs text-warn">
              Δεν ήταν δυνατή η σύνδεση. Έλεγξε το token και δοκίμασε Ανανέωση.
            </p>
          )}
          {snapshotLabels.map((label) => {
            const value =
              label === "Health"
                ? (systemStatus?.status ?? "loading")
                : label === "API connection"
                  ? hasConfiguredNousApi()
                    ? "configured"
                    : "same-origin"
                  : label === "Missions σε εξέλιξη"
                    ? String(systemStatus?.counts?.missions ?? "—")
                    : label === "Tool runs"
                      ? String(systemStatus?.counts?.toolRuns ?? "—")
                      : label === "CPU"
                        ? `${systemStatus?.metrics?.cpu_percent ?? "—"}%`
                        : label === "Memory"
                          ? `${systemStatus?.metrics?.memory_percent ?? "—"}%`
                          : label === "Overview"
                            ? systemStatus?.overview
                              ? "live"
                              : "—"
                            : (systemStatus?.storage ?? "—");
            return (
              <div
                key={label}
                className="flex min-w-0 items-start justify-between gap-3 border-b border-border/60 py-1.5 text-sm last:border-0"
              >
                <span className="min-w-0 break-words text-muted-foreground">{label}</span>
                <span
                  className={`shrink-0 text-right ${label === "Health" && (value === "ok" || value === "online") ? "text-ok" : "text-foreground"}`}
                >
                  {value}
                </span>
              </div>
            );
          })}
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

        <Card title="Missions — ζωντανά">
          <div className="mb-3 flex flex-wrap gap-2 text-[11px]">
            <span className="rounded-full border border-border px-2 py-0.5">
              Ενεργά: {missionSummary.active}
            </span>
            <span className="rounded-full border border-warn/30 px-2 py-0.5 text-warn">
              Θέλουν έγκριση: {missionSummary.awaiting}
            </span>
            <span className="rounded-full border border-destructive/30 px-2 py-0.5 text-destructive">
              Απέτυχαν: {missionSummary.failed}
            </span>
            <span className="text-muted-foreground">
              {liveStatus === "connected"
                ? "Ανανέωση κάθε 3″"
                : liveStatus === "connecting"
                  ? "Σύνδεση…"
                  : "Εκτός σύνδεσης"}
            </span>
          </div>
          <MissionList missions={liveMissions} />
        </Card>

        <Card title="Εγκρίσεις">
          <ApprovalList
            approvals={approvals}
            status={approvalStatus}
            onResolve={resolveApproval}
            onRefresh={loadApprovals}
          />
        </Card>

        <Card title="Υγεία Render & Gemini">
          <HealthPanel
            renderStatus={systemStatus?.status}
            renderState={systemStatusState}
            checkedAt={systemStatusCheckedAt}
            geminiState={geminiTestState}
            geminiMessage={geminiTestMessage}
            missionsLive={liveStatus === "connected"}
            canTestGemini={hasToken}
            onRefresh={() => void loadSystemStatus()}
            onTestGemini={() => void testGeminiConnection()}
          />
        </Card>

        <Card title="Companion">
          {companionStatus ? (
            <div className="space-y-1 text-sm">
              <p>
                Διαθέσιμο:{" "}
                <span className={companionStatus.available ? "text-ok" : "text-warn"}>
                  {companionStatus.available ? "ναι" : "όχι"}
                </span>
              </p>
              {companionStatus.commands?.length ? (
                <p className="text-xs text-muted-foreground">
                  Εντολές: {companionStatus.commands.join(", ")}
                </p>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Δεν ήταν δυνατή η ανάγνωση της κατάστασης του companion.
            </p>
          )}
          <Button
            variant="ghost"
            type="button"
            onClick={() => void loadCompanionStatus()}
            className="mt-3 rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
          >
            Ανανέωση
          </Button>
        </Card>
      </div>

      <div className="mt-4 rounded-2xl border border-violet/40 bg-violet/5 p-5">
        <h3 className="font-display text-base font-semibold">Τι θέλει να κάνει ο ΝΟΥΣ</h3>
        <p className="text-xs text-muted-foreground">Αυτόνομες προτάσεις — έγκρινε ή απόρριψε</p>
        {initiativesState === "error" && (
          <p className="mt-3 text-xs text-warn">
            Δεν ήταν δυνατή η φόρτωση ή εκτέλεση των προτάσεων.
            {failedInitiative && (
              <Button
                variant="ghost"
                type="button"
                disabled={initiativePending}
                className="ml-2 rounded-md border border-warn/50 px-2 py-0.5 font-medium hover:bg-warn/10"
                onClick={() =>
                  void resolveInitiative(failedInitiative.initiative, failedInitiative.action)
                }
              >
                Δοκίμασε ξανά
              </Button>
            )}
          </p>
        )}
        {initiatives.length === 0 ? (
          <div className="mt-4 rounded-xl border border-dashed border-border bg-card/50 p-4 text-sm text-muted-foreground">
            {initiativesState === "loading" ? "Φό��τωση…" : "Δεν υπάρχουν εκκρεμε��ς προτάσεις."}
          </div>
        ) : (
          <div className="mt-4 space-y-2">
            {initiatives.map((initiative) => (
              <div
                key={initiative.id}
                className="rounded-xl border border-border bg-card/60 p-3 text-sm"
              >
                <p className="font-semibold">
                  {initiative.icon} {initiative.title}
                  {initiative.priority && (
                    <span className="ml-2 font-mono text-[10px] uppercase text-warn">
                      {initiative.priority}
                    </span>
                  )}
                </p>
                {initiative.description && (
                  <p className="mt-1 text-xs text-muted-foreground">{initiative.description}</p>
                )}
                <div className="mt-2 flex gap-2">
                  <Button
                    variant="ghost"
                    type="button"
                    disabled={initiativePending || !initiative.approve_route}
                    onClick={() => void resolveInitiative(initiative, "approve")}
                    className="rounded-lg bg-ok/15 px-3 py-1.5 text-xs font-semibold text-ok disabled:opacity-40"
                  >
                    Έγκριση
                  </Button>
                  <Button
                    variant="ghost"
                    type="button"
                    disabled={initiativePending || !initiative.reject_route}
                    onClick={() => void resolveInitiative(initiative, "reject")}
                    className="rounded-lg border border-border px-3 py-1.5 text-xs disabled:opacity-40"
                  >
                    Απόρριψη
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
        <Button
          variant="ghost"
          type="button"
          onClick={() => void loadInitiatives()}
          className="mt-3 rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
        >
          Ανανέωση προτάσεων
        </Button>
      </div>
      <div className="mt-4">
        <SectionPanel section="home" />
      </div>
    </div>
  );
}
