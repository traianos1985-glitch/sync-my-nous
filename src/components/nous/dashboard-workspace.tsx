import { AppSandboxPanel } from "./app-sandbox-panel";
import { BrowserOperatorStudio } from "./browser-operator-studio";
import { ApprovalList } from "@/components/nous/approval-list";
import { sectionConfigs } from "@/components/nous/section-configs";
import { SectionPanel } from "@/components/nous/section-panel";
import { MissionList } from "@/components/nous/mission-list";

import { ScanLine, ShieldAlert } from "lucide-react";
import { navLabel } from "@/components/nous/nav";
import { nousFetch } from "@/lib/nous-api";

import { Button } from "@/components/ui/button";
import { Card } from "./dashboard-primitives";
import type { useDashboard } from "./use-dashboard";
import { KnowledgeIngestionPanel } from "./knowledge-ingestion-panel";
import { ConnectionSettings } from "./dashboard-connection-settings";
import { AppBuilderStudio } from "./app-builder-studio";
import { AutonomyPanel } from "./autonomy-panel";
import { ExecutionReceiptsPanel } from "./execution-receipts-panel";

export function DashboardWorkspace({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const {
    section,
    setSection,
    githubStatus,
    systemStatus,
    hasToken,
    geminiTestState,
    geminiTestMessage,
    systemStatusError,
    liveMissions,
    sentinelError,
    setSentinelError,
    sentinel,
    setSentinel,
    testGeminiConnection,
    checkGithubStatus,
    approvals,
    approvalStatus,
    resolveApproval,
    loadApprovals,
  } = dashboard;
  if (section === "receipts") {
    return (
      <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
        <div className="mx-auto min-w-0 max-w-5xl">
          <Card title="Execution Receipts">
            <ExecutionReceiptsPanel />
          </Card>
        </div>
      </div>
    );
  }
  if (section === "appbuilder")
    return <AppBuilderStudio connected={hasToken} onOpenSandbox={() => setSection("sandbox")} />;
  if (section === "sandbox") {
    return (
      <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
        <div className="mx-auto min-w-0 max-w-6xl">
          <AppSandboxPanel connected={hasToken} />
        </div>
      </div>
    );
  }
  if (section === "browser") {
    return (
      <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
        <div className="mx-auto min-w-0 max-w-6xl">
          <BrowserOperatorStudio connected={hasToken} />
        </div>
      </div>
    );
  }
  if (section === "autonomy") {
    return (
      <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
        <div className="mx-auto min-w-0 max-w-5xl">
          <AutonomyPanel connected={hasToken} />
        </div>
      </div>
    );
  }
  return (
    <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
      <div className="mx-auto grid min-w-0 max-w-5xl gap-4 lg:grid-cols-[1.3fr_0.7fr]">
        <Card title={navLabel(section)}>
          <p className="text-sm text-muted-foreground">
            {section === "missions"
              ? "Οι αποστολές εκτελούνται με checkpoints, logs και έγκριση πριν από κάθε επικίνδυνη ενέργεια."
              : section === "documents"
                ? "Ανέβασε έγγραφα στο knowledge vault ώστε ο NOUS να τα χρησιμοποιεί στο chat."
                : section === "control"
                  ? "Συνδέσεις providers και defensive έλεγχοι του NOUS."
                  : section === "settings"
                    ? "Ρυθμίσεις σύνδεσης του dashboard με το NOUS backend."
                    : `Ζωντανή κατάσταση και ενέργειες της ενότητας ${navLabel(section)} από το NOUS backend.`}
          </p>
          {section === "settings" && (
            <div className="mt-5 space-y-3">
              {!hasToken && (
                <div
                  role="status"
                  className="rounded-xl border border-warn/40 bg-warn/10 p-3 text-xs"
                >
                  Δεν έχει οριστεί NOUS token σε αυτό το browser session. Επικόλλησε το token
                  παρακάτω για να ενεργοποιήσεις τα προστατευμένα endpoints.
                </div>
              )}
              {systemStatus?.status === "degraded" || systemStatus?.status === "unavailable" ? (
                <div
                  role="status"
                  className="rounded-xl border border-warn/40 bg-warn/10 p-3 text-xs"
                >
                  Η επικοινωνία με το Render backend δεν έχει επιβεβαιωθεί ως υγιής.
                  {systemStatusError
                    ? ` Λεπτομέρεια: ${systemStatusError}`
                    : " Έλεγξε τη διεύθυνση API, το token και την κατάσταση του Render."}
                </div>
              ) : null}
              <ConnectionSettings dashboard={dashboard} />
            </div>
          )}
          {sectionConfigs[section] && <SectionPanel section={section} />}
          {section === "documents" && <KnowledgeIngestionPanel dashboard={dashboard} />}
          {section === "control" && (
            <div className="mt-5 space-y-4">
              <div className="rounded-2xl border border-primary/25 bg-primary/5 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary">
                      NOUS control plane
                    </p>
                    <h2 className="mt-2 font-display text-xl font-semibold">
                      Οι συνδέσεις σου, με όρια που ελέγχεις
                    </h2>
                    <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                      Ο NOUS μπορεί να χρησιμοποιεί model providers και repositories, αλλά κάθε
                      εξωτερική αλλαγή παραμένει proposal-first και απαιτεί ρητή έγκριση.
                    </p>
                  </div>
                  <span className="rounded-full border border-ok/30 bg-ok/10 px-2 py-1 font-mono text-[10px] text-ok">
                    APPROVAL REQUIRED
                  </span>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {[
                  {
                    name: "Google Gemini",
                    detail: "Server-side API key στο Render · model reasoning",
                    tone: "text-signal",
                    scope: "Μόνο εγκεκριμένες κλήσεις",
                  },
                  {
                    name: "GitHub",
                    detail: "Repos · branches · pull requests",
                    tone: "text-primary",
                    scope: "Push/merge πάντα με approval",
                  },
                ].map((provider) => (
                  <div
                    key={provider.name}
                    className="rounded-2xl border border-border bg-card/60 p-4"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className={`size-2 rounded-full bg-current ${provider.tone}`} />
                      <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground">
                        {provider.name === "GitHub" ? "GIT STATUS" : "SERVER-SIDE"}
                      </span>
                    </div>
                    <p className="mt-4 font-semibold">{provider.name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{provider.detail}</p>
                    <p className="mt-3 rounded-lg bg-background/60 px-2 py-1.5 text-[11px] text-muted-foreground">
                      {provider.scope}
                    </p>
                    <Button
                      variant="ghost"
                      type="button"
                      onClick={() =>
                        void (provider.name === "GitHub"
                          ? checkGithubStatus()
                          : testGeminiConnection())
                      }
                      disabled={provider.name !== "GitHub" && geminiTestState === "testing"}
                      className="mt-3 w-full rounded-lg border border-border px-3 py-2 text-xs font-semibold transition-colors hover:border-primary/50 hover:bg-primary/5 disabled:opacity-50"
                    >
                      {provider.name === "GitHub"
                        ? "Έλεγχος git στο backend"
                        : geminiTestState === "testing"
                          ? "Έλεγχος Gemini…"
                          : "Έλεγχος σύνδεσης Gemini"}
                    </Button>
                    {(provider.name === "GitHub" ? githubStatus : geminiTestMessage) && (
                      <p
                        className={`mt-2 text-[11px] ${provider.name !== "GitHub" && geminiTestState === "ok" ? "text-ok" : "text-muted-foreground"}`}
                      >
                        {provider.name === "GitHub" ? githubStatus : geminiTestMessage}
                      </p>
                    )}
                  </div>
                ))}
              </div>
              <div className="rounded-2xl border border-primary/25 bg-primary/5 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 font-semibold">
                      <ScanLine className="size-4 text-primary" /> Defensive Sentinel
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Ελέγχει μόνο defensive controls του NOUS· δεν κάνει exploit ή scanning τρίτων.
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    type="button"
                    onClick={async () => {
                      try {
                        setSentinelError(false);
                        setSentinel(await nousFetch<typeof sentinel>("/api/security-audit"));
                      } catch {
                        setSentinel(null);
                        setSentinelError(true);
                      }
                    }}
                    className="rounded-lg border border-primary/30 px-3 py-2 text-xs font-semibold hover:bg-primary/10"
                  >
                    Έλεγχος τώρα
                  </Button>
                </div>
                {sentinelError && (
                  <p className="mt-3 text-xs text-destructive">
                    Ο έλεγχος ασφαλείας δεν είναι διαθέσιμος αυτή τη στιγμή.
                  </p>
                )}
                {sentinel && (
                  <div className="mt-4 grid gap-3 md:grid-cols-[auto_1fr]">
                    <div className="flex size-20 flex-col items-center justify-center rounded-full border-4 border-primary/40">
                      <strong className="text-xl">{sentinel.score}</strong>
                      <span className="font-mono text-[9px] text-muted-foreground">/ 100</span>
                    </div>
                    <div className="space-y-2">
                      {sentinel.findings.length === 0 ? (
                        <p className="rounded-lg bg-ok/10 p-3 text-xs text-ok">
                          Όλα τα ενεργά defensive checks είναι εντάξει.
                        </p>
                      ) : (
                        sentinel.findings.map((finding) => (
                          <div
                            key={finding.id}
                            className="rounded-lg border border-border bg-background/60 p-3"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <strong className="text-xs">{finding.title}</strong>
                              <span className="font-mono text-[9px] uppercase text-muted-foreground">
                                {finding.severity}
                              </span>
                            </div>
                            <p className="mt-1 text-[11px] text-muted-foreground">
                              {finding.detail}
                            </p>
                            <p className="mt-1 text-[11px] text-primary">
                              Fix: {finding.remediation}
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
              <div className="rounded-2xl border border-warn/25 bg-warn/5 p-4 text-sm">
                <div className="flex items-center gap-2 font-semibold text-warn">
                  <ShieldAlert className="size-4" /> Action policy
                </div>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">
                  Read operations μπ��ρούν να προταθούν αυτόματα. Commit, push, merge, delete και
                  external side effects δημιουργούν approval record, diff και audit event πριν
                  εκτελεστούν.
                </p>
              </div>
            </div>
          )}
          <div className="mt-5 space-y-2">
            {section === "missions" && <MissionList missions={liveMissions} />}
            {section === "approvals" && (
              <ApprovalList
                approvals={approvals}
                status={approvalStatus}
                onResolve={resolveApproval}
                onRefresh={loadApprovals}
              />
            )}
          </div>
        </Card>
        <Card title="Agent guardrails">
          <div className="space-y-3 text-sm">
            {["Backend truth checks", "Approval before side effects", "Audit trail enabled"].map(
              (item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="size-2 rounded-full bg-ok" />
                  {item}
                </div>
              ),
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
