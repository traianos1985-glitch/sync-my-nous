import { useCallback, useEffect, useRef, useState } from "react";
import { useDashboardRequests } from "./use-dashboard-requests";
import { nousBlob } from "@/lib/nous-api";
import { runStudioValidation } from "@/lib/app-studio-api";
import {
  appendConsole,
  type RepairDetail,
  type RepairProposal,
  type StudioApp,
  type StudioBuild,
  type ValidationResult,
} from "./app-studio-model";

export function useAppStudio(connected: boolean) {
  const request = useDashboardRequests();
  const [apps, setApps] = useState<StudioApp[]>([]);
  const [builds, setBuilds] = useState<StudioBuild[]>([]);
  const [selected, setSelected] = useState("");
  const [file, setFile] = useState("");
  const [code, setCode] = useState("");
  const [consoleText, setConsoleText] = useState("");
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [repairs, setRepairs] = useState<RepairProposal[]>([]);
  const [repair, setRepair] = useState<RepairDetail | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState("");
  const [approval, setApproval] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const scope = useRef<AbortController | null>(null);
  const actionLock = useRef(false);
  const fileGeneration = useRef(0);
  const validation = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    if (!connected) return;
    setLoading(true);
    try {
      const [files, plans] = await Promise.all([
        request<{ apps: StudioApp[] }>("/remote/app-builder/files"),
        request<{ builds: StudioBuild[] }>("/remote/app-builder/list"),
      ]);
      setApps(files.apps ?? []);
      setBuilds(plans.builds ?? []);
      setSelected((current) =>
        files.apps.some((app) => app.name === current) ? current : (files.apps[0]?.name ?? ""),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Αποτυχία φόρτωσης");
    } finally {
      setLoading(false);
    }
  }, [connected, request]);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    const controller = new AbortController();
    scope.current = controller;
    setFile("");
    setCode("");
    setRepair(null);
    setRepairs([]);
    setResult(null);
    setConsoleText("");
    setApproval(null);
    setRunning(false);
    setLogs("");
    setBusy(null);
    setError("");
    fileGeneration.current += 1;
    if (selected && connected) {
      void request<{ repairs: RepairProposal[] }>(
        `/remote/app-builder/repairs?app=${encodeURIComponent(selected)}`,
        { signal: controller.signal },
      )
        .then((data) => {
          if (!controller.signal.aborted) setRepairs(data.repairs ?? []);
        })
        .catch((e) => {
          if (!controller.signal.aborted) setError(e.message);
        });
      const poll = async () => {
        try {
          const data = await request<{ running: boolean; log: string }>(
            `/remote/app-builder/app-log?app=${encodeURIComponent(selected)}`,
            { signal: controller.signal },
          );
          if (!controller.signal.aborted) {
            setRunning(data.running);
            setLogs(data.log ?? "");
          }
        } catch (e) {
          if (!controller.signal.aborted)
            setError(e instanceof Error ? e.message : "Αποτυχία logs");
        }
        if (!controller.signal.aborted) timer = setTimeout(() => void poll(), 3_000);
      };
      let timer: ReturnType<typeof setTimeout>;
      void poll();
      return () => {
        controller.abort();
        clearTimeout(timer);
        validation.current?.abort();
      };
    }
    return () => {
      controller.abort();
      validation.current?.abort();
    };
  }, [selected, connected, request]);

  async function action(label: string, work: (signal: AbortSignal) => Promise<void>) {
    if (actionLock.current || !connected || !scope.current) return;
    actionLock.current = true;
    setBusy(label);
    setError("");
    const signal = scope.current.signal;
    try {
      await work(signal);
    } catch (e) {
      if (!signal.aborted) setError(e instanceof Error ? e.message : "Η ενέργεια απέτυχε");
    } finally {
      actionLock.current = false;
      if (!signal.aborted) setBusy(null);
    }
  }
  async function post<T extends { ok?: boolean; error?: string; approval_required?: boolean }>(
    path: string,
    body: object,
    signal: AbortSignal,
  ): Promise<T> {
    const data = await request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
      signal,
      timeoutMs: 210_000,
    });
    if (data.ok === false && !data.approval_required)
      throw new Error(data.error ?? "Η ενέργεια απέτυχε");
    return data;
  }
  const selectFile = async (name: string) => {
    const generation = ++fileGeneration.current;
    setFile(name);
    setCode("Φόρτωση…");
    const signal = scope.current?.signal;
    try {
      const data = await request<{ ok: boolean; content: string; error?: string }>(
        `/remote/app-builder/read-file?app=${encodeURIComponent(selected)}&file=${encodeURIComponent(name)}`,
        { signal },
      );
      if (generation !== fileGeneration.current || signal?.aborted) return;
      if (!data.ok) throw new Error(data.error ?? "Αποτυχία ανάγνωσης");
      setCode(data.content);
    } catch (e) {
      if (generation === fileGeneration.current && !signal?.aborted) {
        setCode("");
        setError(e instanceof Error ? e.message : "Αποτυχία ανάγνωσης");
      }
    }
  };
  const openRepair = (id: string) =>
    action("review", async (signal) => {
      const data = await request<RepairDetail>(
        `/remote/app-builder/repair/${encodeURIComponent(id)}`,
        { signal },
      );
      if (!signal.aborted) setRepair(data);
    });
  const test = () =>
    action("tests", async (signal) => {
      const controller = new AbortController();
      validation.current = controller;
      const abort = () => controller.abort();
      signal.addEventListener("abort", abort, { once: true });
      setResult(null);
      setConsoleText("");
      try {
        const data = await runStudioValidation(
          selected,
          (text) => {
            if (!signal.aborted) setConsoleText((current) => appendConsole(current, text));
          },
          { signal: controller.signal },
        );
        if (!signal.aborted) setResult(data);
      } finally {
        signal.removeEventListener("abort", abort);
        validation.current = null;
      }
    });
  const diagnose = () =>
    action("diagnose", async (signal) => {
      const data = await post<{ ok: boolean; repair_id?: string; test_result: ValidationResult }>(
        "/remote/app-builder/diagnose",
        { app_name: selected },
        signal,
      );
      setResult(data.test_result);
      setConsoleText((data.test_result.stdout ?? "") + (data.test_result.stderr ?? ""));
      if (data.repair_id) {
        const detail = await request<RepairDetail>(`/remote/app-builder/repair/${data.repair_id}`, {
          signal,
        });
        setRepair(detail);
        setRepairs((current) => [...current, detail.proposal]);
      }
    });
  const resolveRepair = (approve: boolean) =>
    action("resolve", async (signal) => {
      if (!repair) return;
      await post(
        `/remote/app-builder/repair-${approve ? "approve" : "reject"}`,
        { repair_id: repair.proposal.repair_id },
        signal,
      );
      setRepairs((current) => current.filter((p) => p.repair_id !== repair.proposal.repair_id));
      setRepair(null);
      setCode("");
      setFile("");
      await refresh();
    });
  const run = () =>
    action("run", async (signal) => {
      const data = await post<{ ok: boolean; approval_required: boolean; approval_id: string }>(
        "/remote/app-builder/run-app",
        { app: selected },
        signal,
      );
      if (data.approval_required) setApproval(data.approval_id);
    });
  const resolveRun = (approve: boolean) =>
    action("run-decision", async (signal) => {
      const data = await post<{ ok?: boolean; running?: boolean; output?: string }>(
        approve ? "/remote/operator/approve-app-run" : "/remote/operator/reject",
        { id: approval },
        signal,
      );
      setApproval(null);
      if (approve) {
        setRunning(data.running === true);
        setLogs(data.output ?? "");
      }
    });
  const stop = () =>
    action("stop", async (signal) => {
      await post("/remote/app-builder/stop-app", { app: selected }, signal);
      setRunning(false);
    });
  const download = () =>
    action("download", async (signal) => {
      const blob = await nousBlob(`/remote/app-builder/download/${encodeURIComponent(selected)}`, {
        signal,
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${selected}.zip`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1_000);
    });
  const plan = (description: string) =>
    action("plan", async (signal) => {
      await post("/remote/app-builder/plan", { description }, signal);
      await refresh();
    });
  const resolvePlan = (id: string, approve: boolean) =>
    action("plan-decision", async (signal) => {
      await post(`/remote/app-builder/${approve ? "approve" : "reject"}`, { plan_id: id }, signal);
      await refresh();
    });
  return {
    apps,
    builds,
    selected,
    setSelected,
    file,
    code,
    selectFile,
    consoleText,
    result,
    repairs,
    repair,
    openRepair,
    busy,
    error,
    running,
    logs,
    approval,
    loading,
    refresh,
    test,
    diagnose,
    resolveRepair,
    run,
    resolveRun,
    stop,
    download,
    plan,
    resolvePlan,
    cancel: () => validation.current?.abort(),
  };
}
