import { shouldIgnoreKeyboardShortcut, matchSectionShortcut } from "./command-menu-model";
import { useDashboardRequests } from "./use-dashboard-requests";
import { useChatSessions } from './use-chat-sessions';
import { useEffect, useRef, useState } from "react";
import { stripMarkdown } from "@/lib/strip-markdown";
import { Activity, Sparkles, ScanLine, ShieldCheck, ShieldAlert } from "lucide-react";
import { navGroups } from "./nav";
import { summarizeMissions } from "./mission-status";
import {
  clearNousToken,
  getNousToken,
  hasConfiguredNousApi,
  hasStoredNousToken,
  setNousToken,
} from "@/lib/nous-api";
import {
  initialChat,
  sourcesToCitations,
  type ChatMessage,
  type Citation,
  type SpeechRecognitionLike,
} from "./dashboard-chat-model";

type Initiative = {
  id: string;
  title: string;
  description?: string;
  icon?: string;
  priority?: string;
  approve_route?: string;
  approve_payload?: Record<string, unknown>;
  reject_route?: string;
  reject_payload?: Record<string, unknown>;
};

type SystemStatus = {
  status: string;
  counts?: { missions: number; toolRuns: number };
  storage?: string;
  metrics?: {
    cpu_percent?: number;
    memory_percent?: number;
    disk_free_mb?: number;
    uptime_s?: number;
  };
  overview?: { metrics?: unknown; local_llm?: unknown };
};

export function useDashboard(sessionId?: string) {
  const chatSessions = useChatSessions(sessionId);
  const { messages, setMessages, draft, setDraft, conversationId, setConversationId, chatLoaded, setChatLoaded } = chatSessions;
  const nousFetch = useDashboardRequests();
  const mountedRef = useRef(true);
  const statusBusyRef = useRef(false);
  const approvalsBusyRef = useRef(false);
  const missionsBusyRef = useRef(false);
  const initiativeBusyRef = useRef(false);
  const [initiativePending, setInitiativePending] = useState(false);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);
  const [section, setSection] = useState("chat");
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const goRef = useRef<(id: string) => void>(() => {});

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
        return;
      }
      if (shouldIgnoreKeyboardShortcut(event.target)) {
        return;
      }
      if (event.key === "?" && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        setShortcutsOpen((open) => !open);
        return;
      }
      if (event.altKey && !event.metaKey && !event.ctrlKey) {
        const target = matchSectionShortcut(event.key);
        if (target) {
          event.preventDefault();
          goRef.current(target);
          return;
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
  const [failedInitiative, setFailedInitiative] = useState<{
    initiative: Initiative;
    action: "approve" | "reject";
  } | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [voiceLanguage, setVoiceLanguage] = useState("el-GR");
  const [pushToTalk, setPushToTalk] = useState(false);
  const [thinkingSlow, setThinkingSlow] = useState(false);
  const [initiatives, setInitiatives] = useState<Initiative[]>([]);
  const [initiativesState, setInitiativesState] = useState<"idle" | "loading" | "error">("idle");
  const [companionStatus, setCompanionStatus] = useState<{
    available?: boolean;
    commands?: string[];
  } | null>(null);
  const [githubStatus, setGithubStatus] = useState<string>("");
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const chatAbortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const chatInputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    setHasToken(Boolean(getNousToken()));
    setHasSessionToken(hasStoredNousToken());
  }, []);

  useEffect(() => {
    if (chatLoaded && !isThinking && section === 'chat') chatInputRef.current?.focus();
  }, [chatLoaded, isThinking, section]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isThinking, section]);

  useEffect(() => {
    if (!isThinking) {
      setThinkingSlow(false);
      return;
    }
    const timer = window.setTimeout(() => setThinkingSlow(true), 8000);
    return () => window.clearTimeout(timer);
  }, [isThinking]);

  useEffect(() => {
    void loadSystemStatus();
    void loadEvaluationMetrics();
    void loadKnowledgeDocuments();
    const statusTimer = window.setInterval(() => void loadSystemStatus(), 30_000);
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setVoiceSupported(Boolean(Recognition && "speechSynthesis" in window));
    return () => {
      window.clearInterval(statusTimer);
      if (missionPollRef.current !== null) window.clearTimeout(missionPollRef.current);
      recognitionRef.current?.stop();
      chatAbortRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
    // These loaders intentionally run once on dashboard mount; each loader owns its current API state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const speak = (text: string) => {
    if (!voiceEnabled || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const spoken = stripMarkdown(text);
    if (!spoken) return;
    const utterance = new SpeechSynthesisUtterance(spoken);
    utterance.lang = voiceLanguage;
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  const startListening = () => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition || isListening) return;
    window.speechSynthesis?.cancel();
    const autoSend = pushToTalk;
    const recognition = new Recognition();
    recognition.lang = voiceLanguage;
    recognition.continuous = autoSend;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from({ length: event.results.length }, (_, index) =>
        String(event.results[index]?.[0]?.transcript ?? ""),
      )
        .join(" ")
        .trim();
      if (!transcript) return;
      if (autoSend) void send(transcript);
      else setDraft((current) => `${current} ${transcript}`.trim());
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognitionRef.current = recognition;
    setIsListening(true);
    recognition.start();
  };

  const toggleListening = () => {
    if (isListening) stopListening();
    else startListening();
  };
  const [researchMode, setResearchMode] = useState<"auto" | "off" | "deep">("auto");
  const [connectionMode, setConnectionMode] = useState<"connected" | "degraded" | null>(null);
  const [activeFocus, setActiveFocus] = useState("chat");
  const [approvals, setApprovals] = useState<
    Array<{ id: string; tool: string; input: unknown; createdAt: string }>
  >([]);
  const [approvalStatus, setApprovalStatus] = useState<"idle" | "loading" | "error">("idle");
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [tokenDraft, setTokenDraft] = useState("");
  // Read browser-only session storage after hydration so the server and first client render match.
  const [hasToken, setHasToken] = useState(false);
  const [hasSessionToken, setHasSessionToken] = useState(false);
  const [geminiTestState, setGeminiTestState] = useState<"idle" | "testing" | "ok" | "error">(
    "idle",
  );
  const [geminiTestMessage, setGeminiTestMessage] = useState("");
  const [systemStatusState, setSystemStatusState] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [systemStatusCheckedAt, setSystemStatusCheckedAt] = useState<string | null>(null);
  const [systemStatusError, setSystemStatusError] = useState<string | null>(null);
  const [liveMissions, setLiveMissions] = useState<
    Array<{ id: string; title: string; status: string }>
  >([]);
  const [liveStatus, setLiveStatus] = useState<"idle" | "connecting" | "connected">("idle");
  const missionSummary = summarizeMissions(liveMissions);
  const [jobHistory, setJobHistory] = useState<
    Array<{
      id: string;
      kind: string;
      status: string;
      retryCount: number;
      lastError?: string | null;
      createdAt: string;
      completedAt?: string | null;
    }>
  >([]);
  const [jobHistoryStatus, setJobHistoryStatus] = useState<"idle" | "loading" | "error">("idle");
  const [auditEvents, setAuditEvents] = useState<
    Array<{ id: string; event: string; createdAt: string; tool?: string | null }>
  >([]);
  const [auditStatus, setAuditStatus] = useState<"idle" | "loading" | "error">("idle");
  const [auditFilter, setAuditFilter] = useState("");
  const [sentinelError, setSentinelError] = useState(false);
  const [knowledgeDocuments, setKnowledgeDocuments] = useState<
    Array<{
      id: string;
      originalName: string;
      contentType: string;
      status: string;
      sizeBytes: number;
    }>
  >([]);
  const [knowledgeUpload, setKnowledgeUpload] = useState("idle");
  const [knowledgeLoadStatus, setKnowledgeLoadStatus] = useState<"idle" | "loading" | "error">(
    "idle",
  );
  const [evaluationMetrics, setEvaluationMetrics] = useState<{
    total: number;
    positive: number;
    negative: number;
    satisfactionRate: number | null;
    trend: Array<{ day: string; positive: number; negative: number }>;
  } | null>(null);
  const [evaluationStatus, setEvaluationStatus] = useState<"idle" | "loading" | "error">("idle");
  const [sentinel, setSentinel] = useState<{
    score: number;
    findings: Array<{
      id: string;
      severity: "low" | "medium" | "high";
      title: string;
      detail: string;
      remediation: string;
    }>;
    checkedAt: string;
  } | null>(null);

  const loadKnowledgeDocuments = async () => {
    setKnowledgeLoadStatus("loading");
    try {
      const data = await nousFetch<{ documents: typeof knowledgeDocuments }>("/api/knowledge");
      if (!Array.isArray(data.documents)) throw new Error("Invalid knowledge response");
      setKnowledgeDocuments(data.documents);
      setKnowledgeLoadStatus("idle");
    } catch {
      setKnowledgeLoadStatus("error");
    }
  };

  const loadEvaluationMetrics = async () => {
    setEvaluationStatus("loading");
    try {
      const data = await nousFetch<{ metrics: typeof evaluationMetrics }>("/api/evaluation");
      setEvaluationMetrics(data.metrics);
      setEvaluationStatus("idle");
    } catch {
      setEvaluationStatus("error");
    }
  };

  const exportEvaluation = () => {
    if (!evaluationMetrics) return;
    const rows = [
      ["day", "positive", "negative"],
      ...evaluationMetrics.trend.map((point) => [point.day, point.positive, point.negative]),
    ];
    const csv = rows.map((row) => row.join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `nous-evaluation-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const uploadKnowledgeDocument = async (file: File) => {
    setKnowledgeUpload("uploading");
    const body = new FormData();
    body.append("file", file);
    try {
      await nousFetch("/api/knowledge", { method: "POST", body });
      setKnowledgeUpload("indexed");
      await loadKnowledgeDocuments();
    } catch {
      setKnowledgeUpload("failed");
    }
  };

  const missionPollRef = useRef<number | null>(null);

  const connectMissionStream = async () => {
    if (missionsBusyRef.current) return;
    if (missionPollRef.current !== null) {
      window.clearTimeout(missionPollRef.current);
      missionPollRef.current = null;
    }
    setLiveStatus("connecting");

    const refreshMissions = async (): Promise<boolean> => {
      if (missionsBusyRef.current || !mountedRef.current) return false;
      missionsBusyRef.current = true;
      try {
        const data = await nousFetch<
          | Array<{ id: string; title?: string; name?: string; status?: string }>
          | { missions?: Array<{ id: string; title?: string; name?: string; status?: string }> }
        >("/remote/missions");
        if (!mountedRef.current) return false;
        const missions = Array.isArray(data) ? data : (data.missions ?? []);
        setLiveMissions(
          missions.map((mission) => ({
            id: String(mission.id),
            title: String(mission.title ?? mission.name ?? "Untitled mission"),
            status: String(mission.status ?? "unknown"),
          })),
        );
        setLiveStatus("connected");
        return true;
      } catch {
        if (mountedRef.current) setLiveStatus("idle");
        return false;
      } finally {
        missionsBusyRef.current = false;
      }
    };

    const poll = async () => {
      const ok = await refreshMissions();
      if (ok && mountedRef.current)
        missionPollRef.current = window.setTimeout(() => void poll(), 3_000);
    };
    await poll();
  };

  const loadAuditEvents = async () => {
    setAuditStatus("loading");
    try {
      const query = new URLSearchParams({ days: "30" });
      if (auditFilter.trim()) query.set("event", auditFilter.trim());
      const data = await nousFetch<{ events: typeof auditEvents }>(
        `/api/audit?${query.toString()}`,
      );
      setAuditEvents(data.events);
      setAuditStatus("idle");
    } catch {
      setAuditStatus("error");
    }
  };

  const exportAudit = async () => {
    const query = new URLSearchParams({ days: "30" });
    if (auditFilter.trim()) query.set("event", auditFilter.trim());
    try {
      // Fetch through nousFetch so the API base URL and token are applied.
      const data = await nousFetch<{ events: typeof auditEvents }>(
        `/api/audit?${query.toString()}`,
      );
      const rows = [
        ["id", "event", "tool", "createdAt"],
        ...data.events.map((item) => [item.id, item.event, item.tool ?? "", item.createdAt]),
      ];
      const csv = rows
        .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
        .join("\n");
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `nous-audit-${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setAuditStatus("error");
    }
  };

  const loadJobHistory = async () => {
    setJobHistoryStatus("loading");
    try {
      const data = await nousFetch<{ jobs: typeof jobHistory }>("/api/jobs?limit=20");
      setJobHistory(data.jobs);
      setJobHistoryStatus("idle");
    } catch {
      setJobHistoryStatus("error");
    }
  };

  const updateJob = async (id: string, action: "cancel" | "retry") => {
    try {
      await nousFetch("/api/jobs", { method: "PATCH", body: JSON.stringify({ id, action }) });
      await loadJobHistory();
    } catch {
      setJobHistoryStatus("error");
    }
  };

  const loadSystemStatus = async () => {
    if (statusBusyRef.current) return;
    statusBusyRef.current = true;
    setSystemStatusState("loading");
    setSystemStatusError(null);
    const [healthResult, statusResult, metricsResult, overviewResult] = await Promise.allSettled([
      // This endpoint is mapped by nous-api.ts directly to the Render backend's /health.
      // Keep backend reachability separate from local dashboard/database status.
      nousFetch<{ system?: string; status?: string; ok?: boolean }>("/api/health"),
      nousFetch<SystemStatus>("/api/status"),
      nousFetch<SystemStatus["metrics"]>("/system-info"),
      nousFetch<SystemStatus["overview"]>("/remote/ops/status"),
    ]);

    statusBusyRef.current = false;
    if (!mountedRef.current) return;
    const health = healthResult.status === "fulfilled" ? healthResult.value : undefined;
    const status = statusResult.status === "fulfilled" ? statusResult.value : undefined;
    const metrics = metricsResult.status === "fulfilled" ? metricsResult.value : undefined;
    const overview = overviewResult.status === "fulfilled" ? overviewResult.value : undefined;
    const backendHealthy = Boolean(
      health && (health.system === "healthy" || health.status === "healthy" || health.ok === true),
    );
    const hasAnyData = Boolean(status || metrics || overview);
    const failure = healthResult.status === "rejected" ? healthResult.reason : undefined;
    const detail =
      failure instanceof Error
        ? failure.message
        : "Το Render backend δεν επιβεβαίωσε υγιή κατά��ταση. Έλεγξε τη σύνδεση και το NOUS token.";

    setSystemStatus({
      ...(status ?? {}),
      // Never infer a healthy Render backend from unrelated local DB/metrics success.
      status: backendHealthy
        ? (status?.status ?? "online")
        : hasAnyData
          ? "degraded"
          : "unavailable",
      metrics,
      overview,
    });
    setSystemStatusState(hasAnyData || backendHealthy ? "ready" : "error");
    setSystemStatusError(backendHealthy ? null : detail);
    setSystemStatusCheckedAt(new Date().toISOString());
  };

  const copyDiagnostics = async () => {
    const diagnostics = [
      `NOUS API: ${hasToken ? "configured" : "missing"}`,
      `Runtime: ${systemStatus?.status ?? "checking"}`,
      `Gemini: ${geminiTestState === "ok" ? "connected" : geminiTestState === "error" ? "error" : "not tested"}`,
      `Checked: ${systemStatusCheckedAt ? new Date(systemStatusCheckedAt).toISOString() : "never"}`,
      systemStatusError ? `Error: ${systemStatusError}` : "",
    ]
      .filter(Boolean)
      .join("\\n");
    await navigator.clipboard?.writeText(diagnostics);
  };

  const testGeminiConnection = async () => {
    setGeminiTestState("testing");
    setGeminiTestMessage("");
    try {
      const request = {
        method: "POST",
        body: JSON.stringify({
          message: "Απάντησε ακριβώς με GEMINI_OK",
          prompt: "Απάντησε ακριβώς με GEMINI_OK",
        }),
      };
      let result: {
        answer?: string;
        reply?: string;
        response?: string;
        model?: string;
        source?: string;
        provider?: string;
      };
      try {
        result = await nousFetch<typeof result>("/api/gemini-check", request);
      } catch (error) {
        if (!(error instanceof Error) || !error.message.includes("(404)")) throw error;
        result = await nousFetch<typeof result>("/gemini-check", request);
      }
      const answer = result.answer ?? result.reply ?? result.response ?? "";
      if (result.source !== "gemini" && result.provider !== "gemini") {
        throw new Error("Το NOUS ��πάντησε, αλλά δεν επιβεβαίωσε provider Gemini.");
      }
      if (!answer) throw new Error("Το Gemini επέστρεψε κενή απάντηση.");
      setGeminiTestState("ok");
      setGeminiTestMessage(
        `Επικοινωνία OK${result.model ? ` · ${result.model}` : result.source ? ` · ${result.source}` : ""}`,
      );
    } catch (error) {
      setGeminiTestState("error");
      setGeminiTestMessage(
        error instanceof Error
          ? `Αποτυχία επικοινωνίας: ${error.message}`
          : "Αποτυχία επικοινωνίας. Έλεγξε το Render backend και το NOUS token.",
      );
    }
  };

  const loadApprovals = async () => {
    if (approvalsBusyRef.current) return;
    approvalsBusyRef.current = true;
    setApprovalStatus("loading");
    try {
      const data = await nousFetch<{ approvals?: typeof approvals }>("/api/approvals");
      setApprovals(data.approvals ?? []);
      setApprovalStatus("idle");
    } catch {
      setApprovalStatus("error");
    } finally {
      approvalsBusyRef.current = false;
    }
  };

  const resolveApproval = async (id: string, status: "approved" | "rejected") => {
    try {
      await nousFetch("/api/approvals", {
        method: "PATCH",
        body: JSON.stringify({ id, status }),
      });
    } catch {
      setApprovalStatus("error");
      return;
    }
    if (status === "approved") {
      try {
        await nousFetch("/api/tools/execute", {
          method: "POST",
          body: JSON.stringify({ approvalId: id }),
        });
      } catch {
        setApprovalStatus("error");
      }
    }
    setApprovals((items) => items.filter((item) => item.id !== id));
  };

  // Home keeps approvals and Render health fresh while it is open.
  const loadApprovalsRef = useRef(loadApprovals);
  const loadSystemStatusRef = useRef(loadSystemStatus);
  loadApprovalsRef.current = loadApprovals;
  loadSystemStatusRef.current = loadSystemStatus;
  useEffect(() => {
    if (section !== "home") return;
    const approvalsTimer = window.setInterval(() => void loadApprovalsRef.current(), 15_000);
    const healthTimer = window.setInterval(() => void loadSystemStatusRef.current(), 60_000);
    return () => {
      window.clearInterval(approvalsTimer);
      window.clearInterval(healthTimer);
    };
  }, [section]);

  const send = async (textOverride?: string, options: { retry?: boolean } = {}) => {
    const text = (textOverride ?? draft).trim();
    if (!text || chatAbortRef.current) return;
    const history = messages
      .filter((message) => message.id !== "welcome" && !message.error)
      .slice(-10)
      .map(({ role, text }) => ({ role, text }));
    if (!options.retry) {
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text }]);
    } else {
      setMessages((m) => m.filter((message) => !(message.error && message.retryText === text)));
    }
    if (textOverride === undefined) setDraft("");
    setIsThinking(true);
    const controller = new AbortController();
    chatAbortRef.current = controller;

    try {
      if (!getNousToken() && hasConfiguredNousApi()) {
        throw new Error(
          "Δεν έχει οριστεί NOUS token. Άνοιξε Settings και αποθήκευσ�� το token για να μιλήσεις με τον NOUS.",
        );
      }
      const data = await nousFetch<{
        answer?: string;
        human_answer?: string;
        response?: string;
        text?: string;
        error?: string;
        mode?: string;
        conversation_id?: string | number;
        sources?: unknown;
        citations?: Citation[];
      }>("/api/chat", {
        method: "POST",
        body: JSON.stringify({
          message: text,
          history,
          activeFocus,
          active_focus: activeFocus,
          researchMode,
          research_mode: researchMode,
          conversation_id: conversationId ?? undefined,
        }),
        signal: controller.signal,
        timeoutMs: 120_000,
      });
      if (!mountedRef.current || chatAbortRef.current !== controller) return;
      const answer = data.human_answer ?? data.answer ?? data.response ?? data.text;
      if (!answer) throw new Error(data.error ?? "Ο NOUS επέστρεψε κενή απάντηση.");
      setConnectionMode(data.mode === "degraded" ? "degraded" : "connected");
      if (data.conversation_id !== undefined && data.conversation_id !== null) {
        setConversationId(String(data.conversation_id));
      }
      const citations = data.citations?.length ? data.citations : sourcesToCitations(data.sources);
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: answer,
          citations: citations.length ? citations : undefined,
        },
      ]);
      speak(answer);
    } catch (error) {
      if (!mountedRef.current || chatAbortRef.current !== controller) return;
      if (error instanceof DOMException && error.name === "AbortError") {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            text: "Η απάντηση διακόπηκε.",
            error: true,
            retryText: text,
          },
        ]);
        return;
      }
      console.error("[nous] Chat request failed", error);
      setConnectionMode("degraded");
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: `Δεν πήρα απάντηση από τον NOUS: ${error instanceof Error ? error.message : "άγνωστο σφάλμα"}`,
          error: true,
          retryText: text,
        },
      ]);
    } finally {
      if (chatAbortRef.current === controller) {
        chatAbortRef.current = null;
        if (mountedRef.current) setIsThinking(false);
      }
    }
  };

  const stopChat = () => chatAbortRef.current?.abort();

  const focusChatWithPrompt = (prompt: string) => {
    setSection("chat");
    setDraft(prompt);
    window.requestAnimationFrame(() => chatInputRef.current?.focus());
  };

  const clearChat = () => {
    chatAbortRef.current?.abort();
    chatAbortRef.current = null;
    setIsThinking(false);
    window.speechSynthesis?.cancel();
    setMessages(initialChat);
    setConversationId(null);
    setConnectionMode(null);
    chatSessions.newSession();
  };

  const loadInitiatives = async () => {
    setInitiativesState("loading");
    try {
      const data = await nousFetch<{ initiatives?: Initiative[] }>("/remote/nous-initiatives");
      setInitiatives(data.initiatives ?? []);
      setInitiativesState("idle");
    } catch {
      setInitiativesState("error");
    }
  };

  const resolveInitiative = async (initiative: Initiative, action: "approve" | "reject") => {
    const route = action === "approve" ? initiative.approve_route : initiative.reject_route;
    const payload = action === "approve" ? initiative.approve_payload : initiative.reject_payload;
    if (!route || initiativeBusyRef.current) return;
    initiativeBusyRef.current = true;
    setInitiativePending(true);
    try {
      await nousFetch("/remote/nous-initiatives/act", {
        method: "POST",
        body: JSON.stringify({ action, route, payload: payload ?? {} }),
        timeoutMs: 90_000,
      });
      setFailedInitiative(null);
    } catch {
      setFailedInitiative({ initiative, action });
      setInitiativesState("error");
      return;
    } finally {
      initiativeBusyRef.current = false;
      if (mountedRef.current) setInitiativePending(false);
    }
    await loadInitiatives();
  };

  const loadCompanionStatus = async () => {
    try {
      setCompanionStatus(
        await nousFetch<{ available?: boolean; commands?: string[] }>("/remote/companion/status"),
      );
    } catch {
      setCompanionStatus(null);
    }
  };

  const checkGithubStatus = async () => {
    setGithubStatus("Έλεγχος…");
    try {
      const data = await nousFetch<{ git?: { ok?: boolean; stdout?: string; stderr?: string } }>(
        "/remote/git/status",
      );
      setGithubStatus(
        data.git?.ok
          ? `Git OK${data.git.stdout ? ` · ${data.git.stdout.split("\n")[0]}` : ""}`
          : `Git μη διαθέσιμο στο backend: ${data.git?.stderr?.trim() || "άγνωστο σφάλμα"}`,
      );
    } catch (error) {
      setGithubStatus(error instanceof Error ? error.message : "Αποτυχία ελέγχου git");
    }
  };

  const commandSignals = [
    {
      label: "Brain",
      value: systemStatus?.status === "online" ? "Online" : (systemStatus?.status ?? "—"),
      detail: "άνοιξε Brain & Memory",
      tone: "text-ok",
      icon: Sparkles,
    },
    {
      label: "Missions",
      value: liveStatus === "connected" ? String(liveMissions.length) : "Live",
      detail: liveStatus === "connected" ? "live stream ενεργό" : "σύνδεση live stream",
      tone: "text-primary",
      icon: Activity,
    },
    {
      label: "Memory",
      value: String(knowledgeDocuments.length),
      detail: "έγγραφα στο knowledge vault",
      tone: "text-signal",
      icon: ScanLine,
    },
    {
      label: "Evaluation",
      value:
        evaluationMetrics?.satisfactionRate !== null &&
        evaluationMetrics?.satisfactionRate !== undefined
          ? `${Math.round(evaluationMetrics.satisfactionRate * (evaluationMetrics.satisfactionRate <= 1 ? 100 : 1))}%`
          : "—",
      detail: `${evaluationMetrics?.total ?? 0} αξιολογήσεις`,
      tone: "text-violet-300",
      icon: Activity,
    },
    {
      label: "Guard",
      value: approvals.length ? String(approvals.length) : "Approvals",
      detail: "ουρά εγκρίσεων",
      tone: "text-warn",
      icon: ShieldCheck,
    },
    {
      label: "Jobs",
      value: jobHistory.length ? String(jobHistory.length) : "Jobs",
      detail: "ιστορικό εργασιών",
      tone: "text-primary",
      icon: Activity,
    },
    {
      label: "Audit",
      value: auditEvents.length ? String(auditEvents.length) : "Log",
      detail: "audit 30 ημερών",
      tone: "text-signal",
      icon: ShieldAlert,
    },
    {
      label: "System",
      value:
        systemStatus?.metrics?.cpu_percent !== undefined
          ? `${Math.round(systemStatus.metrics.cpu_percent)}%`
          : "—",
      detail: "CPU / RAM / overview",
      tone: "text-ok",
      icon: ScanLine,
    },
  ];

  const submitFeedback = async (messageId: string, rating: "positive" | "negative") => {
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId ? { ...message, feedback: rating } : message,
      ),
    );
    try {
      await nousFetch("/api/feedback", {
        method: "POST",
        body: JSON.stringify({ messageId, rating }),
      });
    } catch (error) {
      console.error("[nous] Feedback request failed", error);
    }
  };

  const go = (id: string) => {
    setSection(id);
    setMenuOpen(false);
    if (id === "home") {
      void loadSystemStatus();
      void loadInitiatives();
      void loadCompanionStatus();
      void connectMissionStream();
      void loadApprovals();
    }
    if (id === "missions") void connectMissionStream();
    if (id === "documents") void loadKnowledgeDocuments();
  };

  const commandItems = navGroups.flatMap((group) => group.items);
  goRef.current = go;
  return {
    ...chatSessions,
    initiativePending,
    section,
    setSection,
    failedInitiative,
    setFailedInitiative,
    advancedOpen,
    setAdvancedOpen,
    menuOpen,
    setMenuOpen,
    commandOpen,
    setCommandOpen,
    shortcutsOpen,
    setShortcutsOpen,
    messages,
    setMessages,
    draft,
    setDraft,
    isThinking,
    setIsThinking,
    isListening,
    setIsListening,
    voiceEnabled,
    setVoiceEnabled,
    voiceSupported,
    setVoiceSupported,
    voiceLanguage,
    setVoiceLanguage,
    pushToTalk,
    setPushToTalk,
    conversationId,
    setConversationId,
    chatLoaded,
    setChatLoaded,
    thinkingSlow,
    setThinkingSlow,
    initiatives,
    setInitiatives,
    initiativesState,
    setInitiativesState,
    companionStatus,
    setCompanionStatus,
    githubStatus,
    setGithubStatus,
    recognitionRef,
    chatAbortRef,
    chatEndRef,
    chatInputRef,
    speak,
    stopListening,
    startListening,
    toggleListening,
    researchMode,
    setResearchMode,
    connectionMode,
    setConnectionMode,
    activeFocus,
    setActiveFocus,
    approvals,
    setApprovals,
    approvalStatus,
    setApprovalStatus,
    systemStatus,
    setSystemStatus,
    tokenDraft,
    setTokenDraft,
    hasToken,
    setHasToken,
    hasSessionToken,
    setHasSessionToken,
    geminiTestState,
    setGeminiTestState,
    geminiTestMessage,
    setGeminiTestMessage,
    systemStatusState,
    setSystemStatusState,
    systemStatusCheckedAt,
    setSystemStatusCheckedAt,
    systemStatusError,
    setSystemStatusError,
    liveMissions,
    setLiveMissions,
    liveStatus,
    setLiveStatus,
    missionSummary,
    jobHistory,
    setJobHistory,
    jobHistoryStatus,
    setJobHistoryStatus,
    auditEvents,
    setAuditEvents,
    auditStatus,
    setAuditStatus,
    auditFilter,
    setAuditFilter,
    sentinelError,
    setSentinelError,
    knowledgeDocuments,
    setKnowledgeDocuments,
    knowledgeUpload,
    setKnowledgeUpload,
    knowledgeLoadStatus,
    setKnowledgeLoadStatus,
    evaluationMetrics,
    setEvaluationMetrics,
    evaluationStatus,
    setEvaluationStatus,
    sentinel,
    setSentinel,
    loadKnowledgeDocuments,
    loadEvaluationMetrics,
    exportEvaluation,
    uploadKnowledgeDocument,
    missionPollRef,
    connectMissionStream,
    loadAuditEvents,
    exportAudit,
    loadJobHistory,
    updateJob,
    loadSystemStatus,
    copyDiagnostics,
    testGeminiConnection,
    loadApprovals,
    resolveApproval,
    loadApprovalsRef,
    loadSystemStatusRef,
    send,
    stopChat,
    focusChatWithPrompt,
    clearChat,
    loadInitiatives,
    resolveInitiative,
    loadCompanionStatus,
    checkGithubStatus,
    commandSignals,
    submitFeedback,
    go,
    commandItems,
  };
}
