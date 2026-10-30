import { useCallback, useEffect, useRef, useState } from "react";
import { nousFetch } from "@/lib/nous-api";
import {
  type BrowserActionItem,
  type BrowserActionType,
  type BrowserBridgeJob,
  type BrowserBridgeStatus,
  type BrowserDriverStatus,
  type BrowserReadResult,
  type BrowserSearchResult,
  cleanSearchQuery,
  createDefaultActions,
  sanitizeTargetUrl,
} from "./browser-operator-model";

export type BrowserTab = "navigate" | "search" | "driver" | "jobs" | "intelligence";

export function useBrowserOperator(connected: boolean) {
  const [activeTab, setActiveTab] = useState<BrowserTab>("navigate");

  // Navigation & Page Reader state
  const [targetUrl, setTargetUrl] = useState("https://news.ycombinator.com");
  const [isReadingUrl, setIsReadingUrl] = useState(false);
  const [readResult, setReadResult] = useState<BrowserReadResult | null>(null);
  const [readError, setReadError] = useState<string | null>(null);
  const [learnSuccess, setLearnSuccess] = useState<string | null>(null);
  const [isLearning, setIsLearning] = useState(false);

  // Search & Deep Research state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState<"quick" | "deep">("quick");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<BrowserSearchResult | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Driver & Playwright actions state
  const [driverStatus, setDriverStatus] = useState<BrowserDriverStatus | null>(null);
  const [isLoadingDriver, setIsLoadingDriver] = useState(false);
  const [actions, setActions] = useState<BrowserActionItem[]>(() =>
    createDefaultActions("https://news.ycombinator.com"),
  );
  const [isRunningDriver, setIsRunningDriver] = useState(false);
  const [driverResult, setDriverResult] = useState<unknown>(null);
  const [driverError, setDriverError] = useState<string | null>(null);

  // Bridge jobs state
  const [bridgeStatus, setBridgeStatus] = useState<BrowserBridgeStatus | null>(null);
  const [bridgeJobs, setBridgeJobs] = useState<BrowserBridgeJob[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [createJobReason, setCreateJobReason] = useState("Έλεγχος UI και εξαγωγή δεδομένων");
  const [isCreatingJob, setIsCreatingJob] = useState(false);

  // Intelligence & Learned items state
  const [learnedItems, setLearnedItems] = useState<unknown[]>([]);
  const [isLoadingLearned, setIsLoadingLearned] = useState(false);
  const [isTriggeringCycle, setIsTriggeringCycle] = useState(false);
  const [cycleMessage, setCycleMessage] = useState<string | null>(null);

  const mountedRef = useRef(true);

  // --- Fetch Driver Status ---
  const fetchDriverStatus = useCallback(async () => {
    if (!connected) return;
    setIsLoadingDriver(true);
    try {
      const res = await nousFetch<BrowserDriverStatus>("/remote/browser-driver/status");
      if (mountedRef.current && res) {
        setDriverStatus(res);
      }
    } catch {
      // Driver status fetch failed non-fatally
    } finally {
      if (mountedRef.current) setIsLoadingDriver(false);
    }
  }, [connected]);

  // --- Fetch Bridge Jobs ---
  const fetchBridgeJobs = useCallback(async () => {
    if (!connected) return;
    setIsLoadingJobs(true);
    try {
      const [jobsRes, statusRes] = await Promise.all([
        nousFetch<BrowserBridgeJob[]>("/remote/browser-bridge/jobs"),
        nousFetch<BrowserBridgeStatus>("/remote/browser-bridge/status"),
      ]);
      if (mountedRef.current) {
        if (Array.isArray(jobsRes)) {
          setBridgeJobs(jobsRes);
        }
        if (statusRes) {
          setBridgeStatus(statusRes);
        }
      }
    } catch {
      // Bridge jobs fetch failed non-fatally
    } finally {
      if (mountedRef.current) setIsLoadingJobs(false);
    }
  }, [connected]);

  // --- Fetch Learned Items ---
  const fetchLearnedTopics = useCallback(async () => {
    if (!connected) return;
    setIsLoadingLearned(true);
    try {
      const res = await nousFetch<{ items?: unknown[]; learned?: unknown[] }>(
        "/remote/research/learned",
      );
      if (mountedRef.current && res) {
        const items = res.items || res.learned || [];
        setLearnedItems(Array.isArray(items) ? items : []);
      }
    } catch {
      // Learned fetch failed non-fatally
    } finally {
      if (mountedRef.current) setIsLoadingLearned(false);
    }
  }, [connected]);

  // Initial load without synchronous setState in effect body
  useEffect(() => {
    mountedRef.current = true;
    let active = true;

    const initialFetch = async () => {
      if (!connected) return;
      try {
        const [driverRes, jobsRes, bridgeRes, learnedRes] = await Promise.all([
          nousFetch<BrowserDriverStatus>("/remote/browser-driver/status"),
          nousFetch<BrowserBridgeJob[]>("/remote/browser-bridge/jobs"),
          nousFetch<BrowserBridgeStatus>("/remote/browser-bridge/status"),
          nousFetch<{ items?: unknown[]; learned?: unknown[] }>("/remote/research/learned"),
        ]);
        if (!active) return;
        if (driverRes) setDriverStatus(driverRes);
        if (Array.isArray(jobsRes)) setBridgeJobs(jobsRes);
        if (bridgeRes) setBridgeStatus(bridgeRes);
        if (learnedRes) {
          const items = learnedRes.items || learnedRes.learned || [];
          setLearnedItems(Array.isArray(items) ? items : []);
        }
      } catch {
        // Initial fetch handled gracefully
      }
    };

    void initialFetch();

    return () => {
      active = false;
      mountedRef.current = false;
    };
  }, [connected]);

  // --- Read URL Action ---
  const handleReadUrl = useCallback(
    async (urlToRead?: string) => {
      const url = sanitizeTargetUrl(urlToRead || targetUrl);
      if (!url) {
        setReadError("Παρακαλώ εισάγετε μια έγκυρη διεύθυνση URL.");
        return;
      }
      setIsReadingUrl(true);
      setReadError(null);
      setLearnSuccess(null);
      try {
        const res = await nousFetch<BrowserReadResult>("/remote/browser/read-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });
        if (!mountedRef.current) return;
        if (res && res.ok !== false) {
          setReadResult(res);
        } else {
          setReadError(res?.error || "Αποτυχία ανάγνωσης ιστοσελίδας από το backend.");
        }
      } catch (err) {
        if (mountedRef.current) {
          setReadError(err instanceof Error ? err.message : "Σφάλμα δικτύου κατά την ανάγνωση.");
        }
      } finally {
        if (mountedRef.current) setIsReadingUrl(false);
      }
    },
    [targetUrl],
  );

  // --- Learn Read URL to Knowledge ---
  const handleLearnCurrentUrl = useCallback(async () => {
    const url = sanitizeTargetUrl(targetUrl);
    if (!url) return;
    setIsLearning(true);
    setLearnSuccess(null);
    try {
      const res = await nousFetch<{ ok: boolean; message?: string; error?: string }>(
        "/remote/research/learn-topic",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic: url }),
        },
      );
      if (mountedRef.current) {
        if (res && res.ok) {
          setLearnSuccess("Η ιστοσελίδα καταχωρήθηκε με επιτυχία στη μνήμη του NOUS!");
          void fetchLearnedTopics();
        } else {
          setReadError(res?.error || "Αποτυχία καταχώρησης στη μνήμη.");
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setReadError(err instanceof Error ? err.message : "Σφάλμα κατά την καταχώρηση.");
      }
    } finally {
      if (mountedRef.current) setIsLearning(false);
    }
  }, [targetUrl, fetchLearnedTopics]);

  // --- Search Action ---
  const handleSearch = useCallback(
    async (queryOverride?: string) => {
      const q = cleanSearchQuery(queryOverride !== undefined ? queryOverride : searchQuery);
      if (!q) {
        setSearchError("Παρακαλώ εισάγετε έναν όρο αναζήτησης.");
        return;
      }
      setIsSearching(true);
      setSearchError(null);
      try {
        const endpoint =
          searchMode === "deep" ? "/remote/research/query" : "/remote/browser/search";
        const res = await nousFetch<BrowserSearchResult>(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q }),
        });
        if (!mountedRef.current) return;
        if (res && res.ok !== false) {
          setSearchResult(res);
        } else {
          setSearchError(res?.error || "Αποτυχία εκτέλεσης αναζήτησης.");
        }
      } catch (err) {
        if (mountedRef.current) {
          setSearchError(err instanceof Error ? err.message : "Σφάλμα δικτύου κατά την αναζήτηση.");
        }
      } finally {
        if (mountedRef.current) setIsSearching(false);
      }
    },
    [searchQuery, searchMode],
  );

  // --- Driver Actions Management ---
  const addAction = useCallback((type: BrowserActionType) => {
    const newId = `act-${Date.now()}`;
    const newAction: BrowserActionItem = {
      id: newId,
      type,
      selector: type === "click" || type === "fill" ? "button, input, [role='button']" : undefined,
      value: type === "fill" ? "" : undefined,
      description:
        type === "open"
          ? "Πλοήγηση σε URL"
          : type === "click"
            ? "Κλικ σε στοιχείο"
            : type === "fill"
              ? "Συμπλήρωση φόρμας"
              : type === "screenshot"
                ? "Λήψη στιγμιότυπου"
                : "Αναμονή 2s",
    };
    setActions((prev) => [...prev, newAction]);
  }, []);

  const removeAction = useCallback((id: string) => {
    setActions((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const updateAction = useCallback((id: string, patch: Partial<BrowserActionItem>) => {
    setActions((prev) => prev.map((a) => (a.id === id ? { ...a, ...patch } : a)));
  }, []);

  const resetActions = useCallback(() => {
    setActions(createDefaultActions(targetUrl));
  }, [targetUrl]);

  // --- Run Driver Actions ---
  const handleRunDriverActions = useCallback(async () => {
    const url = sanitizeTargetUrl(targetUrl);
    if (!url) {
      setDriverError("Παρακαλώ ορίστε μια έγκυρη αρχική διεύθυνση URL.");
      return;
    }
    setIsRunningDriver(true);
    setDriverError(null);
    setDriverResult(null);
    try {
      const cleanActions = actions.map((a) => ({
        type: a.type,
        selector: a.selector,
        value: a.value,
      }));
      const res = await nousFetch<{ ok?: boolean; error?: string; result?: unknown }>(
        "/remote/browser-driver/run",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, actions: cleanActions }),
        },
      );
      if (!mountedRef.current) return;
      if (res && res.ok !== false) {
        setDriverResult(res);
      } else {
        setDriverError(res?.error || "Αποτυχία εκτέλεσης browser actions.");
      }
    } catch (err) {
      if (mountedRef.current) {
        setDriverError(err instanceof Error ? err.message : "Σφάλμα κατά την εκτέλεση του driver.");
      }
    } finally {
      if (mountedRef.current) setIsRunningDriver(false);
    }
  }, [targetUrl, actions]);

  // --- Create Bridge Job ---
  const handleCreateBridgeJob = useCallback(async () => {
    const url = sanitizeTargetUrl(targetUrl);
    if (!url) {
      setDriverError("Παρακαλώ ορίστε μια έγκυρη διεύθυνση URL.");
      return;
    }
    setIsCreatingJob(true);
    try {
      const cleanActions = actions.map((a) => ({
        type: a.type,
        selector: a.selector,
        value: a.value,
      }));
      const res = await nousFetch<{ ok?: boolean; error?: string }>(
        "/remote/browser-bridge/create",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url,
            actions: cleanActions,
            reason: createJobReason.trim() || "Remote browser job",
          }),
        },
      );
      if (mountedRef.current && res && res.ok !== false) {
        void fetchBridgeJobs();
        setActiveTab("jobs");
      }
    } catch {
      // Create bridge job failed
    } finally {
      if (mountedRef.current) setIsCreatingJob(false);
    }
  }, [targetUrl, actions, createJobReason, fetchBridgeJobs]);

  // --- Trigger Research Cycle ---
  const handleTriggerCycle = useCallback(async () => {
    setIsTriggeringCycle(true);
    setCycleMessage(null);
    try {
      const res = await nousFetch<{ ok: boolean; message?: string; error?: string }>(
        "/remote/research/cycle",
        {
          method: "POST",
        },
      );
      if (mountedRef.current) {
        if (res && res.ok) {
          setCycleMessage("Ο νέος κύκλος έρευνας ενεργοποιήθηκε επιτυχώς!");
          void fetchLearnedTopics();
        } else {
          setCycleMessage(`Αποτυχία: ${res?.error || "Σφάλμα ενεργοποίησης κύκλου."}`);
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setCycleMessage(err instanceof Error ? err.message : "Σφάλμα δικτύου.");
      }
    } finally {
      if (mountedRef.current) setIsTriggeringCycle(false);
    }
  }, [fetchLearnedTopics]);

  return {
    activeTab,
    setActiveTab,
    // Page Reader
    targetUrl,
    setTargetUrl,
    isReadingUrl,
    readResult,
    readError,
    learnSuccess,
    isLearning,
    handleReadUrl,
    handleLearnCurrentUrl,
    // Search
    searchQuery,
    setSearchQuery,
    searchMode,
    setSearchMode,
    isSearching,
    searchResult,
    searchError,
    handleSearch,
    // Driver
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
    // Jobs
    bridgeStatus,
    bridgeJobs,
    isLoadingJobs,
    fetchBridgeJobs,
    createJobReason,
    setCreateJobReason,
    isCreatingJob,
    handleCreateBridgeJob,
    // Intelligence
    learnedItems,
    isLoadingLearned,
    fetchLearnedTopics,
    isTriggeringCycle,
    cycleMessage,
    handleTriggerCycle,
  };
}
