import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertOctagon,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  Copy,
  HeartPulse,
  Loader2,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldAlert,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { nousFetch } from "@/lib/nous-api";
import {
  filterAutonomyEvents,
  formatElapsedSeconds,
  formatEventBadge,
  formatEventTimestamp,
  getWatchdogTone,
  INTERVAL_PRESETS,
  isEmergencyStopped,
  validateInterval,
  type AutonomyEventItem,
  type AutonomyServiceState,
  type WatchdogStatus,
} from "./autonomy-model";

export function AutonomyPanel({ connected }: { connected: boolean }) {
  const [state, setState] = useState<AutonomyServiceState | null>(null);
  const [watchdog, setWatchdog] = useState<WatchdogStatus | null>(null);
  const [events, setEvents] = useState<AutonomyEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [nowSeconds, setNowSeconds] = useState<number>(() => Math.floor(Date.now() / 1000));

  const [intervalInput, setIntervalInput] = useState<string>("300");
  const [intervalError, setIntervalError] = useState<string | null>(null);

  const [filterType, setFilterType] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedEvents, setExpandedEvents] = useState<Record<number, boolean>>({});
  const [copiedTime, setCopiedTime] = useState<number | null>(null);
  const [actionNotice, setActionNotice] = useState<{
    text: string;
    tone: "ok" | "warn" | "destructive";
  } | null>(null);

  const fetchAutonomyData = useCallback(async () => {
    try {
      const [statusRes, watchdogRes, eventsRes] = await Promise.all([
        nousFetch<AutonomyServiceState>("/remote/service/status").catch(() => null),
        nousFetch<WatchdogStatus>("/remote/service/watchdog").catch(() => null),
        nousFetch<{ events: AutonomyEventItem[] }>("/remote/service/events?limit=50").catch(() => ({
          events: [],
        })),
      ]);

      setNowSeconds(Math.floor(Date.now() / 1000));
      if (statusRes) {
        setState(statusRes);
        setIntervalInput((prev) =>
          document.activeElement?.id === "interval-input"
            ? prev
            : String(statusRes.interval ?? 300),
        );
      }
      if (watchdogRes) setWatchdog(watchdogRes);
      if (eventsRes?.events) setEvents(eventsRes.events);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshNow = () => {
    setLoading(true);
    void fetchAutonomyData();
  };

  useEffect(() => {
    void fetchAutonomyData();
  }, [fetchAutonomyData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = window.setInterval(() => {
      void fetchAutonomyData();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [autoRefresh, fetchAutonomyData]);

  const handleEnable = async (overrideInterval?: number) => {
    const valResult = validateInterval(overrideInterval ?? intervalInput);
    if (!valResult.valid) {
      setIntervalError(valResult.error ?? "Μη έγκυρο διάστημα");
      return;
    }
    setIntervalError(null);
    setActionBusy(true);
    setActionNotice(null);
    try {
      const res = await nousFetch<AutonomyServiceState>("/remote/service/enable", {
        method: "POST",
        body: JSON.stringify({ interval: valResult.value }),
      });
      setState(res);
      setActionNotice({
        text: `Ο αυτόνομος κύκλος ενεργοποιήθηκε με διάστημα ${valResult.value}δ.`,
        tone: "ok",
      });
      void fetchAutonomyData();
    } catch (err) {
      setActionNotice({
        text: `Αποτυχία έναρξης: ${err instanceof Error ? err.message : "Σφάλμα επικοινωνίας"}`,
        tone: "destructive",
      });
    } finally {
      setActionBusy(false);
    }
  };

  const handleDisable = async () => {
    setActionBusy(true);
    setActionNotice(null);
    try {
      const res = await nousFetch<AutonomyServiceState>("/remote/service/disable", {
        method: "POST",
      });
      setState(res);
      setActionNotice({ text: "Ο αυτόνομος κύκλος τέθηκε σε παύση.", tone: "warn" });
      void fetchAutonomyData();
    } catch (err) {
      setActionNotice({
        text: `Αποτυχία παύσης: ${err instanceof Error ? err.message : "Σφάλμα επικοινωνίας"}`,
        tone: "destructive",
      });
    } finally {
      setActionBusy(false);
    }
  };

  const handleRunOnce = async () => {
    setActionBusy(true);
    setActionNotice(null);
    try {
      const res = await nousFetch<{
        ok: boolean;
        error?: string;
        skipped?: boolean;
        reason?: string;
      }>("/remote/service/run-once", { method: "POST" });
      if (res.ok) {
        setActionNotice({ text: "Εκτελέστηκε επιτυχώς ένας αυτόνομος κύκλος.", tone: "ok" });
      } else if (res.skipped) {
        setActionNotice({
          text: `Ο κύκλος παραλείφθηκε (λόγος: ${res.reason ?? "ανενεργό"}).`,
          tone: "warn",
        });
      } else {
        setActionNotice({
          text: `Σφάλμα εκτέλεσης κύκλου: ${res.error ?? "άγνωστο σφάλμα"}`,
          tone: "destructive",
        });
      }
      void fetchAutonomyData();
    } catch (err) {
      setActionNotice({
        text: `Αποτυχία: ${err instanceof Error ? err.message : "Σφάλμα επικοινωνίας"}`,
        tone: "destructive",
      });
    } finally {
      setActionBusy(false);
    }
  };

  const handleEmergencyStop = async () => {
    const confirmed = window.confirm(
      "ΠΡΟΣΟΧΗ: Θέλετε να ενεργοποιήσετε το Emergency Stop (Kill Switch);\n\nΌλοι οι αυτόνομοι κύκλοι θα ανασταλούν άμεσα!",
    );
    if (!confirmed) return;

    setActionBusy(true);
    setActionNotice(null);
    try {
      const res = await nousFetch<AutonomyServiceState>("/remote/service/emergency-stop", {
        method: "POST",
        body: JSON.stringify({ reason: "dashboard_kill_switch_triggered" }),
      });
      setState(res);
      setActionNotice({
        text: "EMERGENCY STOP ΕΝΕΡΓΟ: Οι αυτόνομοι κύκλοι διακόπηκαν άμεσα.",
        tone: "destructive",
      });
      void fetchAutonomyData();
    } catch (err) {
      setActionNotice({
        text: `Αποτυχία Emergency Stop: ${err instanceof Error ? err.message : "Σφάλμα"}`,
        tone: "destructive",
      });
    } finally {
      setActionBusy(false);
    }
  };

  const toggleExpand = (time: number) => {
    setExpandedEvents((prev) => ({ ...prev, [time]: !prev[time] }));
  };

  const copyEventPayload = async (time: number, data?: Record<string, unknown>) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data ?? {}, null, 2));
      setCopiedTime(time);
      window.setTimeout(() => setCopiedTime(null), 2000);
    } catch {
      // ignore
    }
  };

  const filteredEvents = useMemo(() => {
    return filterAutonomyEvents(events, filterType, searchQuery);
  }, [events, filterType, searchQuery]);

  const emergencyActive = isEmergencyStopped(state);
  const watchdogTone = getWatchdogTone(watchdog);

  return (
    <div className="space-y-6">
      {/* Top Banner and Header */}
      <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="size-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Autonomy Control & Live Feed</h2>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Κονσόλα διαχείρισης αυτόνομου κύκλου NOUS, heartbeat / watchdog και ζωντανό audit
            timeline.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            type="button"
            onClick={() => setAutoRefresh((prev) => !prev)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-mono transition-colors ${
              autoRefresh
                ? "border-ok/40 bg-ok/10 text-ok hover:bg-ok/20"
                : "border-border text-muted-foreground hover:bg-muted"
            }`}
          >
            <Activity className="mr-1.5 size-3.5" />
            {autoRefresh ? "Live 5s" : "Auto-off"}
          </Button>
          <Button
            variant="outline"
            type="button"
            onClick={refreshNow}
            disabled={loading}
            className="rounded-lg px-3 py-1.5 text-xs"
          >
            <RefreshCw className={`mr-1.5 size-3.5 ${loading ? "animate-spin" : ""}`} />
            Ανανέωση
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
            Για να εκκινήσετε, να παύσετε ή να αλλάξετε ρυθμίσεις του κύκλου απαιτείται token
            διαχειριστή. Μεταβείτε στις Ρυθμίσεις (Settings) για να ορίσετε το token.
          </p>
        </div>
      )}

      {/* Emergency Stop Active Alert */}
      {emergencyActive && (
        <div
          role="alert"
          className="rounded-2xl border-2 border-destructive bg-destructive/10 p-5 text-foreground shadow-sm"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ShieldAlert className="size-6 shrink-0 text-destructive" />
              <div>
                <h3 className="font-display text-base font-bold text-destructive">
                  EMERGENCY STOP ΕΝΕΡΓΟΠΟΙΗΜΕΝΟ
                </h3>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Ο αυτόνομος κύκλος έχει ανασταλεί πλήρως από το kill switch ασφαλείας.
                </p>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              disabled={actionBusy || !connected}
              onClick={() => void handleEnable()}
              className="rounded-xl border-destructive/40 bg-destructive/20 text-xs font-semibold text-destructive hover:bg-destructive/30"
            >
              <RotateCcw className="mr-1.5 size-3.5" />
              Επαναφορά & Εκκίνηση (Reset)
            </Button>
          </div>
        </div>
      )}

      {/* Action Notice feedback */}
      {actionNotice && (
        <div
          className={`rounded-xl border p-3 text-xs font-medium ${
            actionNotice.tone === "ok"
              ? "border-ok/40 bg-ok/10 text-ok"
              : actionNotice.tone === "warn"
                ? "border-warn/40 bg-warn/10 text-warn"
                : "border-destructive/40 bg-destructive/10 text-destructive"
          }`}
        >
          {actionNotice.text}
        </div>
      )}

      {/* Upper Grid Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Card 1: Cycle Control */}
        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              ΚΑΤΑΣΤΑΣΗ ΚΥΚΛΟΥ
            </span>
            <span
              className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${
                emergencyActive
                  ? "border border-destructive/40 bg-destructive/10 text-destructive"
                  : state?.enabled
                    ? "border border-ok/40 bg-ok/10 text-ok"
                    : "border border-warn/40 bg-warn/10 text-warn"
              }`}
            >
              {emergencyActive ? "KILL SWITCH" : state?.enabled ? "ΕΝΕΡΓΟΣ" : "ΣΕ ΠΑΥΣΗ"}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2 text-center">
            <div className="rounded-xl border border-border/60 bg-background/50 p-2.5">
              <span className="text-[10px] uppercase text-muted-foreground">Κύκλοι</span>
              <p className="font-mono text-lg font-bold text-foreground">
                {state?.cycles !== undefined ? state.cycles : "—"}
              </p>
            </div>
            <div className="rounded-xl border border-border/60 bg-background/50 p-2.5">
              <span className="text-[10px] uppercase text-muted-foreground">Τελ. Εκτέλεση</span>
              <p className="font-mono text-xs font-semibold text-foreground">
                {state?.last_run ? formatElapsedSeconds(nowSeconds - state.last_run) : "—"}
              </p>
            </div>
          </div>

          {state?.last_error && (
            <p className="mt-2 rounded-lg bg-destructive/10 p-2 text-center font-mono text-[11px] text-destructive">
              Σφάλμα: {state.last_error}
            </p>
          )}

          {/* Action buttons */}
          <div className="mt-4 space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={actionBusy || !connected || Boolean(state?.enabled)}
                onClick={() => void handleEnable()}
                className="rounded-lg text-xs font-semibold hover:border-ok/50 hover:bg-ok/10"
              >
                {actionBusy ? (
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                ) : (
                  <Play className="mr-1.5 size-3.5 text-ok" />
                )}
                Έναρξη
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={actionBusy || !connected || !state?.enabled}
                onClick={() => void handleDisable()}
                className="rounded-lg text-xs font-semibold hover:border-warn/50 hover:bg-warn/10"
              >
                {actionBusy ? (
                  <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                ) : (
                  <Pause className="mr-1.5 size-3.5 text-warn" />
                )}
                Παύση
              </Button>
            </div>

            <Button
              type="button"
              variant="outline"
              disabled={actionBusy || !connected}
              onClick={() => void handleRunOnce()}
              className="w-full rounded-lg text-xs font-semibold"
            >
              <Clock className="mr-1.5 size-3.5" />
              Εκτέλεση 1 κύκλου τώρα (Run Once)
            </Button>

            <Button
              type="button"
              variant="destructive"
              disabled={actionBusy || !connected}
              onClick={() => void handleEmergencyStop()}
              className="w-full rounded-lg text-xs font-bold tracking-wide"
            >
              <ShieldAlert className="mr-1.5 size-4" />
              EMERGENCY STOP (KILL SWITCH)
            </Button>
          </div>
        </div>

        {/* Card 2: Cycle Interval Settings */}
        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              ΔΙΑΣΤΗΜΑ ΕΚΤΕΛΕΣΗΣ (INTERVAL)
            </span>
            <span className="font-mono text-[10px] text-primary">
              Τρέχον: {state?.interval ?? 300}δ
            </span>
          </div>

          <div className="mt-4">
            <label htmlFor="interval-input" className="text-xs font-medium text-muted-foreground">
              Δευτερόλεπτα ανά κύκλο (5 - 86.400)
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                id="interval-input"
                type="number"
                min={5}
                max={86400}
                value={intervalInput}
                onChange={(e) => {
                  setIntervalInput(e.target.value);
                  setIntervalError(null);
                }}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 font-mono text-sm focus:border-primary focus:outline-none"
              />
              <Button
                type="button"
                variant="outline"
                disabled={actionBusy || !connected}
                onClick={() => void handleEnable()}
                className="shrink-0 rounded-xl px-3 py-2 text-xs font-semibold"
              >
                Αποθήκευση
              </Button>
            </div>
            {intervalError && <p className="mt-1 text-[11px] text-destructive">{intervalError}</p>}
          </div>

          <div className="mt-4">
            <span className="text-[10px] uppercase text-muted-foreground">Γρήγορα Presets</span>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {INTERVAL_PRESETS.map((preset) => (
                <Button
                  key={preset.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={actionBusy || !connected}
                  onClick={() => {
                    setIntervalInput(String(preset.value));
                    void handleEnable(preset.value);
                  }}
                  className={`rounded-lg px-2.5 py-1 font-mono text-xs ${
                    state?.interval === preset.value
                      ? "border-primary bg-primary/10 text-primary"
                      : ""
                  }`}
                >
                  {preset.label} ({preset.value}δ)
                </Button>
              ))}
            </div>
          </div>

          <p className="mt-4 text-[11px] text-muted-foreground">
            Ο κύκλος εκτελεί αυτόνομες αποστολές, μάθηση και master reasoning ανά το επιλεγμένο
            χρονικό διάστημα.
          </p>
        </div>

        {/* Card 3: Watchdog & Heartbeat */}
        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              HEARTBEAT & WATCHDOG
            </span>
            <span
              className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${
                watchdogTone === "ok"
                  ? "border border-ok/40 bg-ok/10 text-ok"
                  : watchdogTone === "warn"
                    ? "border border-warn/40 bg-warn/10 text-warn"
                    : "border border-destructive/40 bg-destructive/10 text-destructive"
              }`}
            >
              {watchdog?.ok ? "WATCHDOG OK" : (watchdog?.action ?? "UNKNOWN")}
            </span>
          </div>

          <div className="mt-4 space-y-2.5">
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-2.5 text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <HeartPulse className="size-3.5 text-primary" /> Σιωπή (Silence)
              </span>
              <strong className="font-mono text-foreground">
                {watchdog?.silence !== undefined ? `${watchdog.silence.toFixed(0)}δ` : "—"}
              </strong>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-2.5 text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="size-3.5 text-primary" /> Τελ. Heartbeat
              </span>
              <strong className="font-mono text-foreground">
                {state?.last_heartbeat
                  ? formatElapsedSeconds(nowSeconds - state.last_heartbeat)
                  : "—"}
              </strong>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-2.5 text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Activity className="size-3.5 text-primary" /> Battery Guard
              </span>
              <strong className="font-mono text-foreground">
                {state?.battery?.status ?? "active"}
              </strong>
            </div>
          </div>

          <p className="mt-4 text-[11px] text-muted-foreground">
            Ο watchdog ελέγχει συνεχή επικοινωνία με το backend service. Αν η σιωπή υπερβεί τα 15
            λεπτά (900δ), σηματοδοτεί ανάγκη επανεκκίνησης.
          </p>
        </div>
      </div>

      {/* Activity Feed / Audit Timeline */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="font-display text-base font-semibold">
              Ζωντανό Activity Feed & Audit Timeline
            </h3>
            <p className="text-xs text-muted-foreground">
              Ιστορικό εκτελέσεων, συμβάντων και αλλαγών κατάστασης του NOUS (από
              data/autonomy.log).
            </p>
          </div>
          <span className="font-mono text-xs text-muted-foreground">
            {filteredEvents.length} / {events.length} συμβάντα
          </span>
        </div>

        {/* Filters and search */}
        <div className="mt-4 flex flex-col gap-2.5 sm:flex-row sm:items-center">
          <div className="flex flex-wrap gap-1">
            {[
              { id: "all", label: "Όλα" },
              { id: "cycles", label: "Κύκλοι" },
              { id: "errors", label: "Σφάλματα" },
              { id: "lifecycle", label: "Κύκλος Ζωής" },
            ].map((f) => (
              <Button
                key={f.id}
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setFilterType(f.id)}
                className={`rounded-lg px-2.5 py-1 text-xs ${
                  filterType === f.id
                    ? "bg-primary/10 font-semibold text-primary"
                    : "text-muted-foreground hover:bg-muted"
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
              placeholder="Αναζήτηση σε συμβάντα και payloads…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-border bg-background py-1.5 pl-8 pr-3 text-xs focus:border-primary focus:outline-none"
            />
          </div>
        </div>

        {/* Timeline List */}
        <div className="mt-4 divide-y divide-border/60">
          {filteredEvents.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Δεν βρέθηκαν συμβάντα που να ταιριάζουν με τα κριτήρια αναζήτησης.
            </div>
          ) : (
            filteredEvents.map((item, idx) => {
              const badge = formatEventBadge(item.event);
              const isExpanded = Boolean(expandedEvents[item.time]);
              const hasData = item.data && Object.keys(item.data).length > 0;

              return (
                <div key={`${item.time}-${idx}`} className="py-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {formatEventTimestamp(item.time)}
                      </span>
                      <span
                        className={`rounded-md px-2 py-0.5 font-mono text-[10px] font-semibold ${
                          badge.tone === "ok"
                            ? "bg-ok/10 text-ok"
                            : badge.tone === "destructive"
                              ? "bg-destructive/10 text-destructive"
                              : badge.tone === "warn"
                                ? "bg-warn/10 text-warn"
                                : badge.tone === "info"
                                  ? "bg-primary/10 text-primary"
                                  : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {badge.label}
                      </span>
                      <span className="font-mono text-xs font-medium text-foreground">
                        {item.event}
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      {hasData && (
                        <Button
                          variant="ghost"
                          size="sm"
                          type="button"
                          onClick={() => toggleExpand(item.time)}
                          className="h-7 px-2 text-[11px] text-muted-foreground"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="mr-1 size-3" /> Απόκρυψη
                            </>
                          ) : (
                            <>
                              <ChevronDown className="mr-1 size-3" /> Δεδομένα
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  </div>

                  {isExpanded && hasData && (
                    <div className="mt-2 rounded-xl border border-border/80 bg-background/80 p-3 font-mono text-[11px]">
                      <div className="flex items-center justify-between pb-1">
                        <span className="text-[10px] uppercase text-muted-foreground">
                          Payload Data
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          type="button"
                          onClick={() => void copyEventPayload(item.time, item.data)}
                          className="h-6 px-2 text-[10px]"
                        >
                          {copiedTime === item.time ? (
                            <>
                              <Check className="mr-1 size-3 text-ok" /> Αντιγράφηκε
                            </>
                          ) : (
                            <>
                              <Copy className="mr-1 size-3" /> Αντιγραφή JSON
                            </>
                          )}
                        </Button>
                      </div>
                      <pre className="overflow-x-auto whitespace-pre-wrap text-muted-foreground">
                        {JSON.stringify(item.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
