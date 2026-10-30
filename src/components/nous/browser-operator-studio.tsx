import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "./dashboard-primitives";
import {
  DEFAULT_WEB_PRESETS,
  estimateWordCount,
  extractReadText,
  formatJobStatus,
  type BrowserActionType,
} from "./browser-operator-model";
import { useBrowserOperator, type BrowserTab } from "./use-browser-operator";
import {
  AlertTriangle,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  ExternalLink,
  Globe,
  Layers,
  ListChecks,
  Loader2,
  Play,
  Plus,
  RotateCw,
  Search,
  Sparkles,
  Terminal,
  Trash2,
} from "lucide-react";

export function BrowserOperatorStudio({ connected }: { connected: boolean }) {
  const {
    activeTab,
    setActiveTab,
    targetUrl,
    setTargetUrl,
    isReadingUrl,
    readResult,
    readError,
    learnSuccess,
    isLearning,
    handleReadUrl,
    handleLearnCurrentUrl,
    searchQuery,
    setSearchQuery,
    searchMode,
    setSearchMode,
    isSearching,
    searchResult,
    searchError,
    handleSearch,
    driverStatus,
    isLoadingDriver,
    fetchDriverStatus,
    actions,
    addAction,
    removeAction,
    updateAction,
    resetActions,
    isRunningDriver,
    driverResult,
    driverError,
    handleRunDriverActions,
    bridgeStatus,
    bridgeJobs,
    isLoadingJobs,
    fetchBridgeJobs,
    createJobReason,
    setCreateJobReason,
    isCreatingJob,
    handleCreateBridgeJob,
    learnedItems,
    isLoadingLearned,
    fetchLearnedTopics,
    isTriggeringCycle,
    cycleMessage,
    handleTriggerCycle,
  } = useBrowserOperator(connected);

  const [showRawJson, setShowRawJson] = useState(false);

  const readText = extractReadText(readResult?.result);
  const wordCount = estimateWordCount(readText);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl border border-border/80 bg-card/60 p-5 backdrop-blur-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex size-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Globe className="size-4" />
              </span>
              <h2 className="font-display text-xl font-bold tracking-tight text-foreground">
                Autonomous Web & Browser Operator
              </h2>
            </div>
            <p className="text-xs text-muted-foreground">
              Αυτόνομη περιήγηση στο web, ανάγνωση & εξαγωγή δεδομένων, deep research και
              αυτοματισμοί Playwright driver.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium border ${
                connected
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-400"
              }`}
            >
              <span
                className={`size-1.5 rounded-full ${connected ? "bg-emerald-400" : "bg-amber-400"}`}
              />
              {connected ? "Render API Connected" : "Απαιτείται NOUS Token"}
            </span>

            {driverStatus && (
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium border ${
                  driverStatus.ready
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                    : "border-border bg-background/50 text-muted-foreground"
                }`}
              >
                <Cpu className="size-3" />
                {driverStatus.ready ? "Driver Active" : "Driver Ready (Node fallback)"}
              </span>
            )}
          </div>
        </div>

        {/* Tab navigation */}
        <div className="mt-5 flex flex-wrap gap-1 border-t border-border/50 pt-3">
          {(
            [
              { id: "navigate", label: "Πλοήγηση & Reader", icon: Compass },
              { id: "search", label: "Web & Deep Research", icon: Search },
              { id: "driver", label: "Playwright Automation", icon: Terminal },
              { id: "jobs", label: "Bridge Worker Jobs", icon: Layers },
              { id: "intelligence", label: "Web Intelligence", icon: BookOpen },
            ] as const
          ).map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as BrowserTab)}
                className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-medium transition-all ${
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="size-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* TAB 1: NAVIGATE & PAGE READER */}
      {activeTab === "navigate" && (
        <div className="space-y-4">
          <Card title="Εξερεύνηση & Ανάγνωση Ιστοσελίδας">
            <div className="space-y-4">
              {/* URL input bar */}
              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                    <Globe className="size-4" />
                  </span>
                  <input
                    type="url"
                    value={targetUrl}
                    onChange={(e) => setTargetUrl(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !isReadingUrl) void handleReadUrl();
                    }}
                    placeholder="https://news.ycombinator.com"
                    className="w-full rounded-xl border border-border bg-background py-2 pl-9 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    onClick={() => void handleReadUrl()}
                    disabled={isReadingUrl || !connected}
                    className="gap-1.5 text-xs"
                  >
                    {isReadingUrl ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <Play className="size-3.5" />
                    )}
                    Ανάγνωση & Εξαγωγή
                  </Button>

                  <a
                    href={targetUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex size-9 items-center justify-center rounded-xl border border-border bg-background text-muted-foreground hover:text-foreground transition-colors"
                    title="Άνοιγμα σε νέα καρτέλα"
                  >
                    <ExternalLink className="size-4" />
                  </a>
                </div>
              </div>

              {/* Presets bar */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-medium text-muted-foreground mr-1">
                  Γρήγοροι στόχοι:
                </span>
                {DEFAULT_WEB_PRESETS.map((preset) => (
                  <button
                    key={preset.url}
                    type="button"
                    onClick={() => {
                      setTargetUrl(preset.url);
                      void handleReadUrl(preset.url);
                    }}
                    className="inline-flex items-center gap-1 rounded-lg border border-border/70 bg-background/50 px-2 py-1 text-[11px] text-muted-foreground hover:border-primary hover:text-foreground transition-colors"
                  >
                    <ArrowUpRight className="size-3 text-primary" />
                    {preset.label}
                  </button>
                ))}
              </div>

              {/* Error & Learn notifications */}
              {readError && (
                <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                  <AlertTriangle className="size-4 shrink-0" />
                  <span>{readError}</span>
                </div>
              )}

              {learnSuccess && (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="size-4 shrink-0" />
                  <span>{learnSuccess}</span>
                </div>
              )}

              {/* Reader Result Output */}
              {readResult && (
                <div className="rounded-xl border border-border/80 bg-background/80 p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2.5">
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">
                        {typeof readResult.result === "object" && readResult.result?.title
                          ? readResult.result.title
                          : "Εξαγμένα Δεδομένα Σελίδας"}
                      </span>
                      <span>•</span>
                      <span>~{wordCount} λέξεις</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => void handleLearnCurrentUrl()}
                        disabled={isLearning}
                        className="gap-1.5 text-xs h-7"
                      >
                        {isLearning ? (
                          <Loader2 className="size-3 animate-spin" />
                        ) : (
                          <Sparkles className="size-3" />
                        )}
                        Αποθήκευση στη Μνήμη
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowRawJson((prev) => !prev)}
                        className="text-xs h-7 text-muted-foreground hover:text-foreground"
                      >
                        {showRawJson ? "Ανάγνωση Κειμένου" : "JSON Data"}
                      </Button>
                    </div>
                  </div>

                  {showRawJson ? (
                    <pre className="max-h-96 overflow-auto rounded-lg bg-card/80 p-3 font-mono text-[11px] text-muted-foreground whitespace-pre-wrap">
                      {JSON.stringify(readResult, null, 2)}
                    </pre>
                  ) : (
                    <div className="max-h-96 overflow-auto pr-2 text-xs leading-relaxed text-foreground whitespace-pre-wrap font-sans">
                      {readText || "Δεν εντοπίστηκε περιεχόμενο κειμένου."}
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 2: SEARCH & DEEP RESEARCH */}
      {activeTab === "search" && (
        <div className="space-y-4">
          <Card title="Μηχανή Αναζήτησης & Deep Research">
            <div className="space-y-4">
              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                  <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                    <Search className="size-4" />
                  </span>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !isSearching) void handleSearch();
                    }}
                    placeholder="π.χ. Τι είναι το WebAssembly System Interface (WASI);"
                    className="w-full rounded-xl border border-border bg-background py-2 pl-9 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div className="flex items-center gap-1.5">
                  <div className="inline-flex rounded-xl border border-border bg-background p-0.5">
                    <button
                      type="button"
                      onClick={() => setSearchMode("quick")}
                      className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                        searchMode === "quick"
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      Quick Web
                    </button>
                    <button
                      type="button"
                      onClick={() => setSearchMode("deep")}
                      className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                        searchMode === "deep"
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      Deep AI Research
                    </button>
                  </div>

                  <Button
                    type="button"
                    onClick={() => void handleSearch()}
                    disabled={isSearching || !connected}
                    className="gap-1.5 text-xs"
                  >
                    {isSearching ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <Search className="size-3.5" />
                    )}
                    Εκτέλεση
                  </Button>
                </div>
              </div>

              {searchError && (
                <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                  <AlertTriangle className="size-4 shrink-0" />
                  <span>{searchError}</span>
                </div>
              )}

              {searchResult && (
                <div className="rounded-xl border border-border/80 bg-background/80 p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-border/50 pb-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="size-4 text-primary" />
                      <span className="text-xs font-semibold text-foreground">
                        {searchResult.source
                          ? `Πηγή: ${searchResult.source}`
                          : "Αποτέλεσμα Έρευνας"}
                      </span>
                    </div>
                    {searchResult.query && (
                      <span className="font-mono text-[10px] text-muted-foreground">
                        «{searchResult.query}»
                      </span>
                    )}
                  </div>

                  <div className="text-xs leading-relaxed text-foreground whitespace-pre-wrap font-sans">
                    {searchResult.answer ||
                      searchResult.result ||
                      "Δεν επιστράφηκε κείμενο απάντησης."}
                  </div>

                  {searchResult.raw != null && typeof searchResult.raw === "object" ? (
                    <details className="mt-2 text-[11px] text-muted-foreground">
                      <summary className="cursor-pointer hover:text-foreground">
                        Προβολή ανεπεξέργαστων δεδομένων
                      </summary>
                      <pre className="mt-2 max-h-60 overflow-auto rounded bg-card p-2 font-mono text-[10px]">
                        {JSON.stringify(searchResult.raw, null, 2)}
                      </pre>
                    </details>
                  ) : null}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 3: PLAYWRIGHT DRIVER & ACTIONS */}
      {activeTab === "driver" && (
        <div className="space-y-4">
          <Card title="Playwright Driver Automation Studio">
            <div className="space-y-4">
              {/* Driver capabilities banner */}
              <div className="rounded-xl border border-border/70 bg-background/60 p-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-xs">
                <div>
                  <p className="font-medium text-foreground">Υποστηριζόμενες ενέργειες Driver:</p>
                  <p className="text-muted-foreground text-[11px]">
                    {driverStatus?.supported_when_ready?.join(", ") ||
                      "open, click, fill, screenshot, wait"}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => void fetchDriverStatus()}
                  disabled={isLoadingDriver}
                  className="gap-1.5 text-xs h-7 self-start sm:self-auto"
                >
                  <RotateCw className={`size-3 ${isLoadingDriver ? "animate-spin" : ""}`} />
                  Έλεγχος Status
                </Button>
              </div>

              {/* Target URL */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-foreground">Αρχική διεύθυνση URL:</label>
                <input
                  type="url"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                  placeholder="https://example.com"
                />
              </div>

              {/* Action Pipeline Builder */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <ListChecks className="size-3.5 text-primary" />
                    Αλληλουχία Ενεργειών ({actions.length}):
                  </span>

                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={resetActions}
                      className="text-xs h-7 text-muted-foreground hover:text-foreground"
                    >
                      Επαναφορά
                    </Button>
                    <div className="flex items-center gap-1">
                      {(["click", "fill", "screenshot"] as BrowserActionType[]).map((type) => (
                        <Button
                          key={type}
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => addAction(type)}
                          className="text-xs h-7 gap-1"
                        >
                          <Plus className="size-3" />
                          {type}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  {actions.map((act, idx) => (
                    <div
                      key={act.id}
                      className="rounded-xl border border-border/80 bg-background/50 p-2.5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="flex size-5 items-center justify-center rounded-full bg-primary/10 text-primary font-mono text-[10px]">
                          {idx + 1}
                        </span>
                        <span className="font-mono text-primary font-medium">
                          {act.type.toUpperCase()}
                        </span>
                        <span className="text-muted-foreground text-[11px]">{act.description}</span>
                      </div>

                      <div className="flex flex-1 items-center gap-2 sm:max-w-md">
                        {(act.type === "click" || act.type === "fill") && (
                          <input
                            type="text"
                            value={act.selector || ""}
                            onChange={(e) => updateAction(act.id, { selector: e.target.value })}
                            placeholder="Selector (π.χ. button#submit)"
                            className="flex-1 rounded-lg border border-border bg-card px-2 py-1 text-[11px] font-mono text-foreground focus:outline-none"
                          />
                        )}
                        {act.type === "fill" && (
                          <input
                            type="text"
                            value={act.value || ""}
                            onChange={(e) => updateAction(act.id, { value: e.target.value })}
                            placeholder="Κείμενο τιμής"
                            className="flex-1 rounded-lg border border-border bg-card px-2 py-1 text-[11px] font-mono text-foreground focus:outline-none"
                          />
                        )}
                        <button
                          type="button"
                          onClick={() => removeAction(act.id)}
                          className="text-muted-foreground hover:text-destructive p-1"
                          title="Διαγραφή ενέργειας"
                        >
                          <Trash2 className="size-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Execution buttons & output */}
              <div className="flex flex-wrap items-center gap-2 pt-2">
                <Button
                  type="button"
                  onClick={() => void handleRunDriverActions()}
                  disabled={isRunningDriver || !connected}
                  className="gap-1.5 text-xs"
                >
                  {isRunningDriver ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Play className="size-3.5" />
                  )}
                  Εκτέλεση Actions (Playwright)
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void handleCreateBridgeJob()}
                  disabled={isCreatingJob || !connected}
                  className="gap-1.5 text-xs"
                >
                  <Layers className="size-3.5" />
                  Αποστολή στο Bridge Queue
                </Button>
              </div>

              {driverError && (
                <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                  <AlertTriangle className="size-4 shrink-0" />
                  <span>{driverError}</span>
                </div>
              )}

              {driverResult !== null && (
                <div className="rounded-xl border border-border/80 bg-background/80 p-3 space-y-1">
                  <p className="text-xs font-semibold text-foreground">
                    Αποτέλεσμα Εκτέλεσης Driver:
                  </p>
                  <pre className="max-h-60 overflow-auto rounded bg-card p-2 font-mono text-[11px] text-muted-foreground">
                    {JSON.stringify(driverResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: BRIDGE WORKER JOBS */}
      {activeTab === "jobs" && (
        <div className="space-y-4">
          <Card title="Remote Browser Bridge Jobs Queue">
            <div className="space-y-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-xs border-b border-border/50 pb-3">
                <div className="flex items-center gap-3">
                  <span className="text-muted-foreground">
                    Λειτουργία:{" "}
                    <strong className="text-foreground">
                      {bridgeStatus?.mode || "worker_queue"}
                    </strong>
                  </span>
                  <span>•</span>
                  <span className="text-muted-foreground">
                    Εκκρεμή:{" "}
                    <strong className="text-foreground">
                      {bridgeStatus?.pending ?? bridgeJobs.length}
                    </strong>
                  </span>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => void fetchBridgeJobs()}
                  disabled={isLoadingJobs}
                  className="gap-1.5 text-xs h-7 self-start sm:self-auto"
                >
                  <RotateCw className={`size-3 ${isLoadingJobs ? "animate-spin" : ""}`} />
                  Ανανέωση
                </Button>
              </div>

              {/* Quick create job */}
              <div className="rounded-xl border border-border/70 bg-background/50 p-3 space-y-2">
                <p className="text-xs font-medium text-foreground">
                  Δημιουργία νέας εργασίας ουράς:
                </p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={createJobReason}
                    onChange={(e) => setCreateJobReason(e.target.value)}
                    placeholder="Αιτιολογία εργασίας (reason)"
                    className="flex-1 rounded-xl border border-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none"
                  />
                  <Button
                    type="button"
                    onClick={() => void handleCreateBridgeJob()}
                    disabled={isCreatingJob || !connected}
                    className="gap-1.5 text-xs"
                  >
                    {isCreatingJob ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <Plus className="size-3.5" />
                    )}
                    Υποβολή Εργασίας
                  </Button>
                </div>
              </div>

              {/* Jobs List */}
              {bridgeJobs.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  Δεν υπάρχουν εκκρεμείς ή αρχειοθετημένες browser bridge εργασίες.
                </div>
              ) : (
                <div className="space-y-2">
                  {bridgeJobs.map((job) => {
                    const st = formatJobStatus(job.status);
                    return (
                      <div
                        key={job.id}
                        className="rounded-xl border border-border/80 bg-background/50 p-3 space-y-1.5 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-primary font-semibold">#{job.id}</span>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-medium border ${
                              st.tone === "green"
                                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                                : st.tone === "blue"
                                  ? "border-sky-500/30 bg-sky-500/10 text-sky-400"
                                  : st.tone === "yellow"
                                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                                    : "border-border bg-card text-muted-foreground"
                            }`}
                          >
                            {st.label}
                          </span>
                        </div>
                        {job.url && (
                          <p className="text-muted-foreground text-[11px] truncate">
                            URL: <span className="text-foreground">{job.url}</span>
                          </p>
                        )}
                        {job.reason && (
                          <p className="text-muted-foreground text-[11px]">{job.reason}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 5: WEB INTELLIGENCE & LEARNED TOPICS */}
      {activeTab === "intelligence" && (
        <div className="space-y-4">
          <Card title="Γνώση που αποκτήθηκε από το Web">
            <div className="space-y-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-xs border-b border-border/50 pb-3">
                <p className="text-muted-foreground">
                  Καταγεγραμμένα θέματα & έρευνες στη μόνιμη μνήμη του NOUS:{" "}
                  <strong className="text-foreground">{learnedItems.length}</strong>
                </p>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => void fetchLearnedTopics()}
                    disabled={isLoadingLearned}
                    className="gap-1.5 text-xs h-7"
                  >
                    <RotateCw className={`size-3 ${isLoadingLearned ? "animate-spin" : ""}`} />
                    Ανανέωση
                  </Button>

                  <Button
                    type="button"
                    size="sm"
                    onClick={() => void handleTriggerCycle()}
                    disabled={isTriggeringCycle || !connected}
                    className="gap-1.5 text-xs h-7"
                  >
                    {isTriggeringCycle ? (
                      <Loader2 className="size-3 animate-spin" />
                    ) : (
                      <Clock className="size-3" />
                    )}
                    Έναρξη Νέου Κύκλου
                  </Button>
                </div>
              </div>

              {cycleMessage && (
                <div className="rounded-xl border border-primary/30 bg-primary/10 p-3 text-xs text-foreground flex items-center gap-2">
                  <Sparkles className="size-4 text-primary shrink-0" />
                  <span>{cycleMessage}</span>
                </div>
              )}

              {learnedItems.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  Δεν υπάρχουν ακόμη καταγεγραμμένα θέματα. Χρησιμοποιήστε την «Αποθήκευση στη
                  Μνήμη» από την καρτέλα Πλοήγησης ή ξεκινήστε νέο κύκλο έρευνας.
                </div>
              ) : (
                <div className="space-y-2">
                  {learnedItems.map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-border/80 bg-background/50 p-3 text-xs space-y-1"
                    >
                      <pre className="font-mono text-[11px] text-muted-foreground whitespace-pre-wrap">
                        {typeof item === "string" ? item : JSON.stringify(item, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
