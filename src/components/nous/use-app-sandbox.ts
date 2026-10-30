import { useCallback, useEffect, useRef, useState } from "react";
import { getNousApiBase, nousBlob, nousFetch } from "@/lib/nous-api";
import type {
  MockEndpointResult,
  SandboxApp,
  SandboxProcessStatus,
  SandboxTestResult,
  SandboxViewport,
} from "./app-sandbox-model";

export function useAppSandbox(connected: boolean) {
  const [apps, setApps] = useState<SandboxApp[]>([]);
  const [selectedAppName, setSelectedAppName] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [processStatus, setProcessStatus] = useState<SandboxProcessStatus>({
    ok: true,
    running: false,
    log: "",
  });
  const [approvalId, setApprovalId] = useState<string | null>(null);

  const [viewport, setViewport] = useState<SandboxViewport>("responsive");
  const [activeTab, setActiveTab] = useState<string>("preview");

  const [testState, setTestState] = useState<{
    running: boolean;
    result?: SandboxTestResult;
    logs: string;
  }>({
    running: false,
    logs: "",
  });

  const [mockResult, setMockResult] = useState<MockEndpointResult | null>(null);
  const [mockBusy, setMockBusy] = useState<boolean>(false);

  const currentApp = apps.find((a) => a.name === selectedAppName) ?? null;
  const pollTimerRef = useRef<number | null>(null);

  const refreshApps = useCallback(async () => {
    if (!connected) {
      setLoading(false);
      return;
    }
    setError(null);
    try {
      setLoading(true);
      const res = await nousFetch<{ ok: boolean; apps?: SandboxApp[]; error?: string }>(
        "/remote/app-builder/files",
      );
      if (res.ok && res.apps) {
        setApps(res.apps);
        setSelectedAppName(
          (prev) => prev || (res.apps && res.apps.length > 0 ? res.apps[0].name : ""),
        );
      } else if (res.error) {
        setError(res.error);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Αποτυχία φόρτωσης εφαρμογών");
    } finally {
      setLoading(false);
    }
  }, [connected]);

  useEffect(() => {
    let mounted = true;
    const initialLoad = async () => {
      if (!connected) {
        setLoading(false);
        return;
      }
      try {
        const res = await nousFetch<{ ok: boolean; apps?: SandboxApp[]; error?: string }>(
          "/remote/app-builder/files",
        );
        if (mounted && res.ok && res.apps) {
          setApps(res.apps);
          setSelectedAppName(
            (prev) => prev || (res.apps && res.apps.length > 0 ? res.apps[0].name : ""),
          );
        }
      } catch (e) {
        if (mounted) setError(e instanceof Error ? e.message : "Αποτυχία φόρτωσης εφαρμογών");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    void initialLoad();
    return () => {
      mounted = false;
    };
  }, [connected]);

  // Poll process logs when an app is selected
  useEffect(() => {
    if (!selectedAppName || !connected) {
      return;
    }

    let active = true;
    const fetchStatus = async () => {
      try {
        const res = await nousFetch<SandboxProcessStatus>(
          `/remote/app-builder/app-log?app=${encodeURIComponent(selectedAppName)}`,
        );
        if (active) {
          setProcessStatus(res);
        }
      } catch {
        // keep previous state if transient network blip
      }
      if (active) {
        pollTimerRef.current = window.setTimeout(() => void fetchStatus(), 2500);
      }
    };

    void fetchStatus();

    return () => {
      active = false;
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [selectedAppName, connected]);

  const selectApp = (name: string) => {
    setSelectedAppName(name);
    setProcessStatus({ ok: true, running: false, log: "" });
    setApprovalId(null);
    setMockResult(null);
  };

  const launchApp = async () => {
    if (!selectedAppName || !connected) return;
    setBusy("launch");
    setError(null);
    try {
      const res = await nousFetch<{
        ok?: boolean;
        approval_required?: boolean;
        approval_id?: string;
        running?: boolean;
        error?: string;
        output?: string;
      }>("/remote/app-builder/run-app", {
        method: "POST",
        body: JSON.stringify({ app: selectedAppName }),
      });

      if (res.approval_required && res.approval_id) {
        setApprovalId(res.approval_id);
      } else if (res.ok) {
        setProcessStatus((prev) => ({
          ...prev,
          running: Boolean(res.running),
          log: res.output ?? prev.log,
        }));
      } else if (res.error) {
        setError(res.error);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Αποτυχία εκκίνησης εφαρμογής");
    } finally {
      setBusy(null);
    }
  };

  const resolveApproval = async (approve: boolean) => {
    if (!approvalId || !connected) return;
    setBusy("approval");
    setError(null);
    try {
      const res = await nousFetch<{ ok?: boolean; running?: boolean; output?: string }>(
        approve ? "/remote/operator/approve-app-run" : "/remote/operator/reject",
        {
          method: "POST",
          body: JSON.stringify({ id: approvalId }),
        },
      );
      setApprovalId(null);
      if (approve) {
        setProcessStatus((prev) => ({
          ...prev,
          running: res.running === true,
          log: res.output ?? prev.log,
        }));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Αποτυχία απόφασης έγκρισης");
    } finally {
      setBusy(null);
    }
  };

  const stopApp = async () => {
    if (!selectedAppName || !connected) return;
    setBusy("stop");
    setError(null);
    try {
      await nousFetch<{ ok: boolean; error?: string }>("/remote/app-builder/stop-app", {
        method: "POST",
        body: JSON.stringify({ app: selectedAppName }),
      });
      setProcessStatus((prev) => ({ ...prev, running: false }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Αποτυχία διακοπής εφαρμογής");
    } finally {
      setBusy(null);
    }
  };

  const restartApp = async () => {
    await stopApp();
    await new Promise((r) => setTimeout(r, 600));
    await launchApp();
  };

  const downloadZip = async () => {
    if (!selectedAppName || !connected) return;
    setBusy("download");
    setError(null);
    try {
      const blob = await nousBlob(
        `/remote/app-builder/download/${encodeURIComponent(selectedAppName)}`,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedAppName}.zip`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Αποτυχία λήψης αρχείου zip");
    } finally {
      setBusy(null);
    }
  };

  const runAutomatedTests = async () => {
    if (!selectedAppName || !connected) return;
    setTestState({ running: true, logs: "Εκτέλεση σουίτας δοκιμών..." });
    setError(null);
    try {
      const res = await nousFetch<{
        ok: boolean;
        test_result?: SandboxTestResult;
        error?: string;
      }>("/remote/app-builder/test", {
        method: "POST",
        body: JSON.stringify({ app_name: selectedAppName }),
      });

      if (res.ok && res.test_result) {
        setTestState({
          running: false,
          result: res.test_result,
          logs:
            (res.test_result.stdout ?? "") +
            (res.test_result.stderr ? `\n[STDERR]\n${res.test_result.stderr}` : ""),
        });
      } else {
        setTestState({
          running: false,
          logs: res.error ?? "Οι δοκιμές απέτυχαν",
          result: { ok: false, status: "failed", error: res.error },
        });
      }
    } catch (e) {
      setTestState({
        running: false,
        logs: e instanceof Error ? e.message : "Σφάλμα εκτέλεσης δοκιμών",
        result: { ok: false, status: "error" },
      });
    }
  };

  const executeMockRequest = async (req: {
    method: "GET" | "POST" | "PUT" | "DELETE";
    path: string;
    body?: string;
  }) => {
    if (!selectedAppName) return;
    setMockBusy(true);
    setMockResult(null);
    const start = performance.now();

    const cleanPath = req.path.startsWith("/") ? req.path : `/${req.path}`;
    const targetUrl = `${getNousApiBase()}/apps/${selectedAppName}${cleanPath === "/" ? "/" : cleanPath}`;

    try {
      const fetchOpts: RequestInit = {
        method: req.method,
        headers: {
          Accept: "application/json, text/plain, */*",
          ...(req.body ? { "Content-Type": "application/json" } : {}),
        },
        body: req.method !== "GET" && req.body ? req.body : undefined,
      };

      const res = await fetch(targetUrl, fetchOpts);
      const text = await res.text();
      const elapsed = Math.round(performance.now() - start);

      const headersObj: Record<string, string> = {};
      res.headers.forEach((v, k) => {
        headersObj[k] = v;
      });

      setMockResult({
        status: res.status,
        statusText: res.statusText,
        durationMs: elapsed,
        body: text,
        headers: headersObj,
      });
    } catch (e) {
      const elapsed = Math.round(performance.now() - start);
      setMockResult({
        status: 0,
        statusText: "Connection Error",
        durationMs: elapsed,
        body: "",
        error:
          e instanceof Error
            ? e.message
            : "Αποτυχία σύνδεσης με την εφαρμογή. Βεβαιωθείτε ότι η εφαρμογή εκτελείται στο Sandbox.",
      });
    } finally {
      setMockBusy(false);
    }
  };

  const getWebPreviewUrl = () => {
    if (!selectedAppName) return "";
    return `${getNousApiBase()}/apps/${selectedAppName}/`;
  };

  return {
    apps,
    selectedAppName,
    setSelectedAppName: selectApp,
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
  };
}
