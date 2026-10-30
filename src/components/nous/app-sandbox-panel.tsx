import { useState } from "react";
import {
  Activity,
  AlertOctagon,
  ArrowRight,
  Box,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  Code2,
  Copy,
  Download,
  ExternalLink,
  FlaskConical,
  Laptop,
  Loader2,
  Maximize2,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  Smartphone,
  Square,
  Tablet,
  Terminal,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DEFAULT_MOCK_PRESETS,
  detectEntryFile,
  filterSandboxLogs,
  formatSandboxDuration,
  getViewportWidth,
  hasWebPreview,
  type MockRequestPreset,
  type SandboxViewport,
} from "./app-sandbox-model";
import { useAppSandbox } from "./use-app-sandbox";

export function AppSandboxPanel({ connected }: { connected: boolean }) {
  const sandbox = useAppSandbox(connected);
  const {
    apps,
    selectedAppName,
    setSelectedAppName,
    currentApp,
    loading,
    busy,
    error,
    processStatus,
    approvalId,
    viewport,
    setViewport,
    activeTab,
    setActiveTab,
    testState,
    mockResult,
    mockBusy,
    refreshApps,
    launchApp,
    resolveApproval,
    stopApp,
    restartApp,
    downloadZip,
    runAutomatedTests,
    executeMockRequest,
    getWebPreviewUrl,
  } = sandbox;

  const [iframeKey, setIframeKey] = useState(0);
  const [logFilter, setLogFilter] = useState<"all" | "errors" | "info">("all");
  const [logSearch, setLogSearch] = useState("");
  const [copiedLog, setCopiedLog] = useState(false);

  // Mock Request state
  const [mockMethod, setMockMethod] = useState<"GET" | "POST" | "PUT" | "DELETE">("GET");
  const [mockPath, setMockPath] = useState("/");
  const [mockBody, setMockBody] = useState("");
  const [showHeaders, setShowHeaders] = useState(false);

  const isRunning = Boolean(processStatus.running);
  const appHasWeb = currentApp ? hasWebPreview(currentApp.files) : false;
  const entryFile = currentApp ? detectEntryFile(currentApp.files) : "—";
  const previewUrl = getWebPreviewUrl();

  const handleApplyPreset = (preset: MockRequestPreset) => {
    setMockMethod(preset.method);
    setMockPath(preset.path);
    setMockBody(preset.body ?? "");
  };

  const handleCopyLogs = async () => {
    try {
      await navigator.clipboard.writeText(processStatus.log ?? "");
      setCopiedLog(true);
      setTimeout(() => setCopiedLog(false), 2000);
    } catch {
      // ignore
    }
  };

  const filteredLogs = filterSandboxLogs(processStatus.log ?? "", logFilter).filter((line) =>
    logSearch ? line.toLowerCase().includes(logSearch.toLowerCase()) : true,
  );

  return (
    <div className="space-y-6">
      {/* Header & App Selection */}
      <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-primary/30 bg-primary/10 p-2.5 text-primary">
            <Box className="size-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-display text-xl font-bold">App Sandbox & Live Runner</h2>
              <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 font-mono text-[10px] text-primary">
                INTERACTIVE
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Εκτέλεση, δοκιμή endpoints, αυτόματα tests και ασφαλής προεπισκόπηση των εφαρμογών του
              NOUS.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label="Επιλογή εφαρμογής"
            value={selectedAppName}
            onChange={(e) => setSelectedAppName(e.target.value)}
            disabled={loading || apps.length === 0}
            className="h-9 rounded-xl border border-border bg-background px-3 font-mono text-xs focus:border-primary focus:outline-none"
          >
            {apps.length === 0 ? (
              <option value="">Δεν υπάρχουν εφαρμογές</option>
            ) : (
              apps.map((app) => (
                <option key={app.name} value={app.name}>
                  {app.name} ({app.file_count} αρχεία)
                </option>
              ))
            )}
          </select>

          <Button
            variant="outline"
            size="sm"
            type="button"
            onClick={() => void refreshApps()}
            disabled={loading}
            className="rounded-xl"
            title="Ανανέωση εφαρμογών"
          >
            <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {!connected && (
        <div
          role="status"
          className="rounded-xl border border-warn/40 bg-warn/10 p-4 text-xs text-foreground"
        >
          <div className="flex items-center gap-2 font-semibold text-warn">
            <AlertOctagon className="size-4" /> Δεν έχει οριστεί NOUS Token
          </div>
          <p className="mt-1 text-muted-foreground">
            Για να εκκινήσετε διεργασίες και να εκτελέσετε δοκιμές στο Sandbox απαιτείται token
            διαχειριστή στις Ρυθμίσεις.
          </p>
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive"
        >
          {error}
        </div>
      )}

      {/* Approval Required Banner */}
      {approvalId && (
        <div
          role="alert"
          className="rounded-2xl border-2 border-warn/80 bg-warn/10 p-4 text-foreground shadow-sm"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <ShieldCheck className="size-5 text-warn" />
              <div>
                <h3 className="font-semibold text-warn">Απαιτείται Έγκριση Εκτέλεσης (App Run)</h3>
                <p className="text-xs text-muted-foreground">
                  Η εκκίνηση της υποδιεργασίας για την εφαρμογή{" "}
                  <strong className="text-foreground">{selectedAppName}</strong> απαιτεί ρητή
                  έγκριση χειριστή.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                disabled={Boolean(busy)}
                onClick={() => void resolveApproval(true)}
                className="rounded-lg text-xs"
              >
                <Check className="mr-1.5 size-3.5" /> Έγκριση Run
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={Boolean(busy)}
                onClick={() => void resolveApproval(false)}
                className="rounded-lg text-xs"
              >
                <X className="mr-1.5 size-3.5" /> Απόρριψη
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Process Control Bar */}
      {currentApp && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-card/60 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span
                className={`size-2.5 rounded-full ${
                  isRunning ? "animate-pulse bg-ok" : "bg-muted-foreground/50"
                }`}
              />
              <span className="font-mono text-xs font-semibold">
                {isRunning ? (
                  <span className="text-ok">
                    ΣΕ ΕΚΤΕΛΕΣΗ {processStatus.pid ? `(PID: ${processStatus.pid})` : ""}
                  </span>
                ) : (
                  <span className="text-muted-foreground">ΣΤΑΜΑΤΗΜΕΝΗ</span>
                )}
              </span>
            </div>

            <span className="hidden text-border sm:inline">•</span>

            <span className="font-mono text-xs text-muted-foreground">
              Entry: <span className="text-foreground">{entryFile}</span>
            </span>

            {currentApp.run_command && (
              <span className="hidden rounded-lg bg-background/80 px-2.5 py-1 font-mono text-[11px] text-primary md:inline">
                {currentApp.run_command}
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {!isRunning ? (
              <Button
                type="button"
                size="sm"
                disabled={Boolean(busy) || !connected}
                onClick={() => void launchApp()}
                className="rounded-xl text-xs font-semibold"
              >
                {busy === "launch" ? (
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                ) : (
                  <Play className="mr-1.5 size-3.5 text-ok" />
                )}
                Launch
              </Button>
            ) : (
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={Boolean(busy) || !connected}
                onClick={() => void stopApp()}
                className="rounded-xl border-warn/40 text-xs font-semibold text-warn hover:bg-warn/10"
              >
                {busy === "stop" ? (
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                ) : (
                  <Square className="mr-1.5 size-3.5" />
                )}
                Stop
              </Button>
            )}

            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={Boolean(busy) || !connected}
              onClick={() => void restartApp()}
              className="rounded-xl text-xs"
              title="Επανεκκίνηση εφαρμογής"
            >
              <RotateCcw className="size-3.5" />
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={Boolean(busy) || !connected}
              onClick={() => void downloadZip()}
              className="rounded-xl text-xs"
              title="Λήψη πηγαίου κώδικα ZIP"
            >
              <Download className="mr-1.5 size-3.5" /> ZIP
            </Button>
          </div>
        </div>
      )}

      {/* Main Tabs Workspace */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid h-auto w-full grid-cols-2 p-1 sm:grid-cols-4">
          <TabsTrigger value="preview" className="rounded-lg py-2 text-xs font-medium">
            <ExternalLink className="mr-1.5 size-3.5" /> Web Preview
          </TabsTrigger>
          <TabsTrigger value="tester" className="rounded-lg py-2 text-xs font-medium">
            <Activity className="mr-1.5 size-3.5" /> API & Mock Tester
          </TabsTrigger>
          <TabsTrigger value="tests" className="rounded-lg py-2 text-xs font-medium">
            <FlaskConical className="mr-1.5 size-3.5" /> Test Runner
          </TabsTrigger>
          <TabsTrigger value="logs" className="rounded-lg py-2 text-xs font-medium">
            <Terminal className="mr-1.5 size-3.5" /> Live Terminal
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Web Preview Frame */}
        <TabsContent value="preview" className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-muted-foreground">Viewport:</span>
              {(
                [
                  { id: "responsive", label: "Auto", icon: Maximize2 },
                  { id: "desktop", label: "Desktop", icon: Laptop },
                  { id: "tablet", label: "Tablet", icon: Tablet },
                  { id: "mobile", label: "Mobile", icon: Smartphone },
                ] as const
              ).map((v) => {
                const Icon = v.icon;
                return (
                  <Button
                    key={v.id}
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setViewport(v.id as SandboxViewport)}
                    className={`h-7 px-2 text-xs ${
                      viewport === v.id
                        ? "bg-primary/10 font-semibold text-primary"
                        : "text-muted-foreground"
                    }`}
                  >
                    <Icon className="mr-1 size-3" /> {v.label}
                  </Button>
                );
              })}
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIframeKey((k) => k + 1)}
                className="h-7 text-xs"
              >
                <RefreshCw className="mr-1 size-3" /> Επαναφόρτωση
              </Button>
              {previewUrl && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  asChild
                  className="h-7 text-xs text-primary"
                >
                  <a href={previewUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-1 size-3" /> Νέα καρτέλα
                  </a>
                </Button>
              )}
            </div>
          </div>

          {/* Sandbox Frame Container */}
          <div className="flex min-h-[500px] w-full justify-center overflow-auto rounded-2xl border border-border bg-background/50 p-2">
            {appHasWeb ? (
              <iframe
                key={iframeKey}
                title={`Sandbox Preview: ${selectedAppName}`}
                src={previewUrl}
                sandbox="allow-scripts allow-forms allow-same-origin allow-modals"
                style={{ width: getViewportWidth(viewport), minHeight: "520px" }}
                className="rounded-xl border border-border bg-card shadow-sm transition-all duration-200"
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <Code2 className="size-10 text-muted-foreground/60" />
                <h3 className="mt-3 font-display text-base font-semibold">
                  Backend / CLI Υπηρεσία
                </h3>
                <p className="mt-1 max-w-md text-xs text-muted-foreground">
                  Η εφαρμογή <strong>{selectedAppName}</strong> δεν περιλαμβάνει αρχείο{" "}
                  <code>index.html</code> για γραφική προεπισκόπηση. Εκτελείται ως αυτόνομο backend
                  / script.
                </p>
                <div className="mt-4 flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveTab("tester")}
                  >
                    Δοκιμή Endpoints (API Tester) <ArrowRight className="ml-1.5 size-3.5" />
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveTab("logs")}
                  >
                    Προβολή Logs <Terminal className="ml-1.5 size-3.5" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Tab 2: API & Mock Tester */}
        <TabsContent value="tester" className="space-y-4">
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="font-display text-base font-semibold">API & Endpoint Tester</h3>
                <p className="text-xs text-muted-foreground">
                  Αποστολή δοκιμαστικών αιτημάτων (HTTP Mock Probe) στην εκτελούμενη εφαρμογή του
                  Sandbox.
                </p>
              </div>
              <span className="font-mono text-xs text-muted-foreground">
                Target: {previewUrl || "—"}
              </span>
            </div>

            {/* Presets */}
            <div className="mt-4">
              <span className="text-[10px] uppercase text-muted-foreground">Έτοιμα Presets:</span>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {DEFAULT_MOCK_PRESETS.map((preset) => (
                  <Button
                    key={preset.name}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleApplyPreset(preset)}
                    className="h-7 text-xs font-mono"
                  >
                    <span className="font-bold text-primary">{preset.method}</span> {preset.name}
                  </Button>
                ))}
              </div>
            </div>

            {/* Request inputs */}
            <div className="mt-4 grid gap-2 sm:grid-cols-[110px_1fr_auto]">
              <select
                aria-label="HTTP Method"
                value={mockMethod}
                onChange={(e) => setMockMethod(e.target.value as "GET" | "POST" | "PUT" | "DELETE")}
                className="h-9 rounded-xl border border-border bg-background px-3 font-mono text-xs font-bold text-primary focus:outline-none"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>

              <input
                type="text"
                value={mockPath}
                onChange={(e) => setMockPath(e.target.value)}
                placeholder="/api/data ή /health"
                className="h-9 rounded-xl border border-border bg-background px-3 font-mono text-xs focus:border-primary focus:outline-none"
              />

              <Button
                type="button"
                disabled={mockBusy || !selectedAppName}
                onClick={() =>
                  void executeMockRequest({
                    method: mockMethod,
                    path: mockPath,
                    body: mockBody.trim() || undefined,
                  })
                }
                className="h-9 rounded-xl text-xs font-semibold"
              >
                {mockBusy ? (
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                ) : (
                  <Play className="mr-1.5 size-3.5" />
                )}
                Αποστολή (Send)
              </Button>
            </div>

            {/* JSON Body editor for POST/PUT */}
            {mockMethod !== "GET" && (
              <div className="mt-3">
                <label htmlFor="mock-body" className="text-xs font-medium text-muted-foreground">
                  JSON Request Body (προαιρετικό):
                </label>
                <textarea
                  id="mock-body"
                  value={mockBody}
                  onChange={(e) => setMockBody(e.target.value)}
                  placeholder='{\n  "key": "value"\n}'
                  rows={3}
                  className="mt-1 w-full rounded-xl border border-border bg-background p-3 font-mono text-xs focus:border-primary focus:outline-none"
                />
              </div>
            )}

            {/* Response result card */}
            {mockResult && (
              <div className="mt-5 rounded-xl border border-border bg-background p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-md px-2 py-0.5 font-mono text-xs font-bold ${
                        mockResult.status >= 200 && mockResult.status < 300
                          ? "bg-ok/10 text-ok"
                          : "bg-destructive/10 text-destructive"
                      }`}
                    >
                      {mockResult.status > 0
                        ? `${mockResult.status} ${mockResult.statusText}`
                        : "ERROR"}
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">
                      <Clock className="mr-1 inline size-3" />
                      {mockResult.durationMs}ms
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    {mockResult.headers && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowHeaders((prev) => !prev)}
                        className="h-6 text-[11px] text-muted-foreground"
                      >
                        {showHeaders ? (
                          <>
                            <ChevronUp className="mr-1 size-3" /> Headers
                          </>
                        ) : (
                          <>
                            <ChevronDown className="mr-1 size-3" /> Headers
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>

                {showHeaders && mockResult.headers && (
                  <div className="my-2 max-h-32 overflow-auto rounded-lg bg-card/60 p-2 font-mono text-[10px] text-muted-foreground">
                    {Object.entries(mockResult.headers).map(([k, v]) => (
                      <div key={k}>
                        <strong className="text-foreground">{k}:</strong> {v}
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-3">
                  <span className="text-[10px] uppercase text-muted-foreground">
                    Response Payload:
                  </span>
                  {mockResult.error ? (
                    <p className="mt-1 font-mono text-xs text-destructive">{mockResult.error}</p>
                  ) : (
                    <pre className="mt-1 max-h-64 overflow-auto rounded-lg bg-card p-3 font-mono text-xs leading-5">
                      {mockResult.body || "(Κενή απάντηση)"}
                    </pre>
                  )}
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Tab 3: Test Runner */}
        <TabsContent value="tests" className="space-y-4">
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="font-display text-base font-semibold">
                  Αυτοματοποιημένος Έλεγχος (Test Runner)
                </h3>
                <p className="text-xs text-muted-foreground">
                  Εκτέλεση σουίτας δοκιμών και στατικής ανάλυσης της επιλεγμένης εφαρμογής.
                </p>
              </div>

              <Button
                type="button"
                disabled={testState.running || !selectedAppName || !connected}
                onClick={() => void runAutomatedTests()}
                className="rounded-xl text-xs font-semibold"
              >
                {testState.running ? (
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                ) : (
                  <FlaskConical className="mr-1.5 size-3.5" />
                )}
                Εκτέλεση Tests
              </Button>
            </div>

            {testState.result && (
              <div className="mt-4 flex items-center gap-3">
                <span
                  className={`rounded-full px-3 py-1 font-mono text-xs font-bold ${
                    testState.result.ok
                      ? "border border-ok/40 bg-ok/10 text-ok"
                      : "border border-destructive/40 bg-destructive/10 text-destructive"
                  }`}
                >
                  {testState.result.ok ? "TESTS PASSED" : "TESTS FAILED"}
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  Διάρκεια: {formatSandboxDuration(testState.result.duration_seconds)}
                </span>
              </div>
            )}

            <div className="mt-4">
              <span className="text-[10px] uppercase text-muted-foreground">
                Test Output Console:
              </span>
              <pre
                role="log"
                className="mt-1.5 h-80 overflow-auto rounded-xl border border-border bg-background p-4 font-mono text-xs leading-5"
              >
                {testState.logs || "Δεν έχουν εκτελεστεί δοκιμές ακόμη."}
              </pre>
            </div>
          </div>
        </TabsContent>

        {/* Tab 4: Live Terminal & Logs */}
        <TabsContent value="logs" className="space-y-4">
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="font-display text-base font-semibold">Ζωντανό Terminal & Logs</h3>
                <p className="text-xs text-muted-foreground">
                  Αναμετάδοση ροής εξόδου (stdout / stderr) της τρέχουσας διεργασίας του Sandbox.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => void handleCopyLogs()}
                  className="rounded-xl text-xs"
                >
                  {copiedLog ? (
                    <>
                      <Check className="mr-1.5 size-3 text-ok" /> Αντιγράφηκε
                    </>
                  ) : (
                    <>
                      <Copy className="mr-1.5 size-3" /> Αντιγραφή
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Filter and search */}
            <div className="mt-4 flex flex-col gap-2.5 sm:flex-row sm:items-center">
              <div className="flex gap-1">
                {(
                  [
                    { id: "all", label: "Όλα" },
                    { id: "errors", label: "Σφάλματα" },
                    { id: "info", label: "Πληροφορίες" },
                  ] as const
                ).map((f) => (
                  <Button
                    key={f.id}
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setLogFilter(f.id)}
                    className={`rounded-lg px-2.5 py-1 text-xs ${
                      logFilter === f.id
                        ? "bg-primary/10 font-semibold text-primary"
                        : "text-muted-foreground"
                    }`}
                  >
                    {f.label}
                  </Button>
                ))}
              </div>

              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 size-3.5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Αναζήτηση σε γραμμές terminal..."
                  value={logSearch}
                  onChange={(e) => setLogSearch(e.target.value)}
                  className="w-full rounded-xl border border-border bg-background py-1.5 pl-8 pr-3 text-xs focus:border-primary focus:outline-none"
                />
              </div>
            </div>

            {/* Terminal Output */}
            <div className="mt-4 overflow-hidden rounded-xl border border-border/80 bg-background font-mono text-xs">
              <div className="flex items-center justify-between border-b border-border/60 bg-muted/40 px-3 py-1.5 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <Terminal className="size-3 text-primary" /> stdout/stderr
                </span>
                <span>{filteredLogs.length} γραμμές</span>
              </div>
              <pre role="log" className="h-96 overflow-auto p-4 leading-5 text-muted-foreground">
                {filteredLogs.length > 0 ? (
                  filteredLogs.map((line, idx) => (
                    <div
                      key={idx}
                      className={
                        /error|fail|exception/i.test(line)
                          ? "text-destructive"
                          : /warn/i.test(line)
                            ? "text-warn"
                            : "text-foreground/90"
                      }
                    >
                      {line}
                    </div>
                  ))
                ) : (
                  <span className="text-muted-foreground/60">
                    (Κανένα διαθέσιμο αρχείο καταγραφής)
                  </span>
                )}
              </pre>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
