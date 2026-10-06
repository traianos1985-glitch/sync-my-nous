import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { ChatMarkdown } from "@/components/nous/chat-markdown";
import { sectionConfigs } from "@/components/nous/section-configs";
import { SectionPanel } from "@/components/nous/section-panel";
import { stripMarkdown } from "@/lib/strip-markdown";
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
  Menu,
  RotateCcw,
  ScanLine,
  Send,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Square,
  X,
  UploadCloud,
} from "lucide-react";
import { navGroups, navLabel } from "@/components/nous/nav";
import {
  clearNousToken,
  getNousToken,
  hasConfiguredNousApi,
  nousFetch,
  nousStream,
  setNousToken,
} from "@/lib/nous-api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "NOUS AI OS — Dashboard & Chat workspace" },
      {
        name: "description",
        content:
          "Το workspace του NOUS AI OS: chat με τον agent, missions, brain & memory, app builder, documents και έλεγχος συστήματος σε μία οθόνη.",
      },
      { property: "og:title", content: "NOUS AI OS — Dashboard" },
      {
        property: "og:description",
        content: "Chat, missions, μνήμη, app builder και έλεγχος συστήματος σε ένα workspace.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

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

type Citation = {
  title: string;
  url: string;
  domain: string;
  sourceType?: string;
  retrievedAt?: string;
};

type SpeechRecognitionEventLike = Event & {
  results: { length: number; [index: number]: { [index: number]: { transcript: string } } };
};
type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}
type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  feedback?: "positive" | "negative";
  error?: boolean;
  retryText?: string;
};

const chatStorageKey = "nous-chat-v1";

function loadStoredChat(): { messages: ChatMessage[]; conversationId: string | null } | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(chatStorageKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { messages?: ChatMessage[]; conversationId?: string | null };
    if (!Array.isArray(parsed.messages) || parsed.messages.length === 0) return null;
    return { messages: parsed.messages, conversationId: parsed.conversationId ?? null };
  } catch {
    return null;
  }
}

function sourcesToCitations(sources: unknown): Citation[] {
  if (!Array.isArray(sources)) return [];
  const citations: Citation[] = [];
  for (const source of sources) {
    const raw =
      typeof source === "string"
        ? source
        : source && typeof source === "object"
          ? ((source as { url?: string; document?: string }).url ??
            (source as { document?: string }).document)
          : undefined;
    if (!raw || !/^https?:\/\//.test(raw)) continue;
    try {
      const url = new URL(raw);
      const title = (source as { title?: string }).title ?? url.hostname;
      if (!citations.some((citation) => citation.url === url.href)) {
        citations.push({ title, url: url.href, domain: url.hostname.replace(/^www\./, "") });
      }
    } catch {
      continue;
    }
  }
  return citations;
}

const initialChat: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    text: "Καλώς ήρθες. Είμαι ο NOUS. Μπορώ να συζητήσω φυσικά, να αναλύσω στόχους, να προτείνω βήματα και —όταν είναι συνδεδεμένο το backend— να εκτελέσω εγκεκριμένες ενέργειες. Δεν θα παρουσιάσω ποτέ μια πρόταση ως ολοκληρωμένη ενέργεια χωρίς επιβεβαίωση.",
  },
];

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

function Dashboard() {
  const [section, setSection] = useState("chat");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [messages, setMessages] = useState(initialChat);
  const [draft, setDraft] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [voiceLanguage, setVoiceLanguage] = useState("el-GR");
  const [pushToTalk, setPushToTalk] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatLoaded, setChatLoaded] = useState(false);
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
    const stored = loadStoredChat();
    if (stored) {
      setMessages(stored.messages);
      setConversationId(stored.conversationId);
    }
    setChatLoaded(true);
  }, []);

  useEffect(() => {
    if (!chatLoaded) return;
    try {
      window.localStorage.setItem(chatStorageKey, JSON.stringify({ messages, conversationId }));
    } catch {
      // Storage full or disabled: chat still works for this page view.
    }
  }, [messages, conversationId, chatLoaded]);

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
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setVoiceSupported(Boolean(Recognition && "speechSynthesis" in window));
    return () => {
      recognitionRef.current?.stop();
      chatAbortRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
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
  const [hasToken, setHasToken] = useState(() => Boolean(getNousToken()));
  const [geminiTestState, setGeminiTestState] = useState<"idle" | "testing" | "ok" | "error">(
    "idle",
  );
  const [geminiTestMessage, setGeminiTestMessage] = useState("");
  const [systemStatusState, setSystemStatusState] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [liveMissions, setLiveMissions] = useState<
    Array<{ id: string; title: string; status: string }>
  >([]);
  const [liveStatus, setLiveStatus] = useState<"idle" | "connecting" | "connected">("idle");
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
    try {
      const data = await nousFetch<{ documents: typeof knowledgeDocuments }>("/api/knowledge");
      setKnowledgeDocuments(data.documents);
    } catch {
      setKnowledgeDocuments([]);
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

  const connectMissionStream = async () => {
    if (liveStatus === "connecting" || liveStatus === "connected") return;
    setLiveStatus("connecting");
    try {
      const response = await nousStream("/api/missions/stream");
      if (!response.body) throw new Error("stream unavailable");
      setLiveStatus("connected");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const event of events) {
          const line = event.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;
          const data = JSON.parse(line.slice(6)) as
            { missions?: typeof liveMissions } | typeof liveMissions;
          // Tolerate both {missions: [...]} and a bare array payload.
          setLiveMissions(Array.isArray(data) ? data : (data.missions ?? []));
        }
      }
      // Stream ended normally: allow the user to reconnect.
      setLiveStatus("idle");
    } catch {
      setLiveStatus("idle");
    }
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
    setSystemStatusState("loading");
    try {
      const [statusResult, metricsResult, overviewResult] = await Promise.allSettled([
        nousFetch<SystemStatus>("/api/status"),
        nousFetch<SystemStatus["metrics"]>("/api/system/metrics"),
        nousFetch<SystemStatus["overview"]>("/api/system/overview"),
      ]);
      const status = statusResult.status === "fulfilled" ? statusResult.value : undefined;
      const metrics = metricsResult.status === "fulfilled" ? metricsResult.value : undefined;
      const overview = overviewResult.status === "fulfilled" ? overviewResult.value : undefined;
      if (status || metrics || overview) {
        setSystemStatus({
          ...(status ?? {}),
          status: status?.status ?? "online",
          metrics,
          overview,
        });
        setSystemStatusState("ready");
        return;
      }
      throw new Error("NOUS system status unavailable");
    } catch {
      try {
        const health = await nousFetch<{ status: string }>("/api/health");
        setSystemStatus({ status: health.status === "healthy" ? "online" : "degraded" });
        setSystemStatusState("ready");
      } catch {
        setSystemStatus({ status: "unavailable" });
        setSystemStatusState("error");
      }
    }
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
        throw new Error("Το NOUS απάντησε, αλλά δεν επιβεβαίωσε provider Gemini.");
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
    setApprovalStatus("loading");
    try {
      const data = await nousFetch<{ approvals?: typeof approvals }>("/api/approvals");
      setApprovals(data.approvals ?? []);
      setApprovalStatus("idle");
    } catch {
      setApprovalStatus("error");
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

  const send = async (textOverride?: string, options: { retry?: boolean } = {}) => {
    const text = (textOverride ?? draft).trim();
    if (!text || isThinking) return;
    const history = messages
      .filter((message) => message.id !== "welcome" && !message.error)
      .slice(-10)
      .map(({ role, text: content }) => ({ role, content }));
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
          "Δεν έχει οριστεί NOUS token. Άνοιξε Settings και αποθήκευσε το token για να μιλήσεις με τον NOUS.",
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
          researchMode,
          research_mode: researchMode,
          conversation_id: conversationId ?? undefined,
        }),
        signal: controller.signal,
        timeoutMs: 120_000,
      });
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
      chatAbortRef.current = null;
      setIsThinking(false);
    }
  };

  const stopChat = () => chatAbortRef.current?.abort();

  const clearChat = () => {
    chatAbortRef.current?.abort();
    window.speechSynthesis?.cancel();
    setMessages(initialChat);
    setConversationId(null);
    setConnectionMode(null);
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
    if (!route) return;
    try {
      await nousFetch("/remote/nous-initiatives/act", {
        method: "POST",
        body: JSON.stringify({ action, route, payload: payload ?? {} }),
        timeoutMs: 90_000,
      });
    } catch {
      setInitiativesState("error");
      return;
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
    }
    if (id === "missions") void connectMissionStream();
    if (id === "documents") void loadKnowledgeDocuments();
  };

  const tokenForm = (
    <form
      className="mb-3 flex flex-col gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (!tokenDraft.trim()) return;
        try {
          setNousToken(tokenDraft);
          setTokenDraft("");
          setHasToken(true);
          setGeminiTestState("idle");
          setGeminiTestMessage("");
          void loadSystemStatus();
        } catch (error) {
          setGeminiTestState("error");
          setGeminiTestMessage(error instanceof Error ? error.message : "Μη έγκυρο NOUS token.");
        }
      }}
    >
      <label htmlFor="nous-token" className="text-xs text-muted-foreground">
        NOUS API token{" "}
        {hasToken ? (
          <span className="text-primary">· αποθηκευμένο σε αυτόν τον browser</span>
        ) : (
          <span className="text-warn">· δεν έχει οριστεί</span>
        )}
      </label>
      <div className="flex min-w-0 flex-wrap gap-2">
        <input
          id="nous-token"
          type="password"
          autoComplete="off"
          value={tokenDraft}
          onChange={(event) => setTokenDraft(event.target.value)}
          placeholder={hasToken ? "Νέο token για αντικατάσταση" : "Επικόλλησε το token"}
          className="w-full min-w-0 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-violet sm:w-auto sm:flex-1"
        />
        <button
          type="submit"
          disabled={!tokenDraft.trim()}
          className="shrink-0 rounded-lg bg-violet px-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          Αποθήκευση
        </button>
        {hasToken && (
          <button
            type="button"
            onClick={() => {
              clearNousToken();
              setHasToken(Boolean(getNousToken()));
              setGeminiTestState("idle");
              setGeminiTestMessage("");
              void loadSystemStatus();
            }}
            className="shrink-0 rounded-lg border border-border px-3 text-sm text-muted-foreground"
          >
            Αφαίρεση
          </button>
        )}
      </div>
      <p className="text-[11px] text-muted-foreground">
        Το token είναι password field και μένει μόνο στο session του browser.
      </p>
      <button
        type="button"
        onClick={() => void testGeminiConnection()}
        disabled={!hasToken || geminiTestState === "testing"}
        className="self-start rounded-lg border border-primary/40 px-3 py-2 text-xs font-semibold text-primary disabled:opacity-50"
      >
        {geminiTestState === "testing" ? "Έλεγχος Gemini…" : "Έλεγχος επικοινωνίας με Gemini"}
      </button>
      {geminiTestMessage && (
        <p className={`text-xs ${geminiTestState === "ok" ? "text-ok" : "text-warn"}`}>
          {geminiTestMessage}
        </p>
      )}
    </form>
  );

  return (
    <div className="flex h-dvh min-h-0 w-full min-w-0 max-w-full overflow-hidden bg-background font-sans text-foreground">
      {/* Sidebar */}
      {menuOpen && (
        <button
          aria-label="Κλείσε το μενού"
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-40 bg-black/55 lg:hidden"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-card/95 transition-transform lg:static lg:translate-x-0 ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-start justify-between px-4 pb-3 pt-4">
          <div>
            <p className="font-display text-base font-bold tracking-tight">🧠 NOUS AI OS</p>
            <p className="mt-0.5 text-xs text-muted-foreground">Personal agent workspace</p>
          </div>
          <button
            onClick={() => setMenuOpen(false)}
            className="text-muted-foreground lg:hidden"
            aria-label="Κλείσε"
          >
            <X className="size-4" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2 pb-2">
          {navGroups
            .filter((g) => !g.advanced)
            .map((group, gi) => (
              <div key={group.title ?? gi}>
                {group.title && (
                  <p className="px-2.5 pb-1 pt-3 font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                    {group.title}
                  </p>
                )}
                {group.items.map((item) => (
                  <NavButton
                    key={item.id}
                    item={item}
                    active={section === item.id}
                    onClick={() => go(item.id)}
                  />
                ))}
                {gi === 0 && <div className="my-2 h-px bg-border" />}
              </div>
            ))}

          <div className="my-2 h-px bg-border" />
          <button
            onClick={() => setAdvancedOpen((o) => !o)}
            className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            ⋯ Προχωρημένα
            <span className="ml-auto text-[10px]">{advancedOpen ? "▾" : "▸"}</span>
          </button>
          {advancedOpen &&
            navGroups
              .filter((g) => g.advanced)
              .map((group) => (
                <div key={group.title}>
                  <p className="px-2.5 pb-1 pt-3 font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                    {group.title}
                  </p>
                  {group.items.map((item) => (
                    <NavButton
                      key={item.id}
                      item={item}
                      active={section === item.id}
                      onClick={() => go(item.id)}
                    />
                  ))}
                </div>
              ))}
        </nav>

        <div className="border-t border-border px-3 py-3">
          <StatBar
            label="CPU"
            pct={Math.round(systemStatus?.metrics?.cpu_percent ?? 0)}
            color="bg-violet"
          />
          <StatBar
            label="RAM"
            pct={Math.round(systemStatus?.metrics?.memory_percent ?? 0)}
            color="bg-primary"
          />
        </div>
      </aside>

      {/* Main */}
      <main className="flex min-w-0 max-w-full flex-1 flex-col">
        <header className="flex min-w-0 shrink-0 items-center justify-between gap-3 border-b border-border/70 bg-card/70 px-4 py-3 backdrop-blur-xl">
          <div className="flex min-w-0 items-center gap-3">
            <button
              onClick={() => setMenuOpen(true)}
              className="rounded-md border border-border p-1.5 lg:hidden"
              aria-label="Άνοιξε το μενού"
            >
              <Menu className="size-4" />
            </button>
            <strong className="font-display text-sm">{navLabel(section)}</strong>
            <span
              className={`rounded-full border border-border px-2.5 py-0.5 font-mono text-xs ${systemStatus?.status === "degraded" || systemStatus?.status === "unavailable" ? "text-warn" : "text-ok"}`}
            >
              health: {systemStatus?.status ?? "checking"}
            </span>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <span className="hidden rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-muted-foreground sm:block">
              Owner Mode
            </span>
            <Link
              to="/"
              className="rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-primary hover:bg-accent"
            >
              info
            </Link>
          </div>
        </header>

        {section === "chat" ? (
          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            <div className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
              <div className="mx-auto max-w-4xl">
                <div className="mb-6 flex items-start justify-between gap-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-primary">
                      <span className="size-1.5 rounded-full bg-primary shadow-[0_0_14px_var(--primary)]" />
                      Agent online · Owner workspace
                    </div>
                    <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
                      Τι αναλαμβάνουμε σήμερα;
                    </h1>
                    <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                      Στόχοι, missions, browser operator και κώδικας — σε μία ενιαία ροή με έγκριση
                      πριν από κάθε εξωτερική ενέργεια.
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
                <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {commandSignals.map(({ icon: Icon, label, value, detail, tone }) => (
                    <button
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
                      className={`group rounded-xl border p-3 text-left transition-all ${activeFocus === label.toLowerCase() ? "border-primary/60 bg-primary/10 shadow-[0_0_24px_oklch(0.68_0.19_292_/_12%)]" : "border-border/70 bg-card/60 hover:border-primary/40"}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted-foreground">
                          {label}
                        </span>
                        <Icon className={`size-3.5 ${tone}`} />
                      </div>
                      <p className={`mt-2 font-display text-lg font-semibold ${tone}`}>{value}</p>
                      <p className="mt-0.5 truncate text-[10px] text-muted-foreground">{detail}</p>
                    </button>
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
                        <button
                          type="button"
                          onClick={() => void loadEvaluationMetrics()}
                          className="rounded-md border border-border px-2.5 py-1.5 text-xs hover:border-primary"
                        >
                          {evaluationStatus === "loading" ? "Φόρτωση…" : "Ανανέωση"}
                        </button>
                        <button
                          type="button"
                          onClick={exportEvaluation}
                          disabled={!evaluationMetrics}
                          className="rounded-md border border-border px-2.5 py-1.5 text-xs hover:border-primary disabled:opacity-40"
                        >
                          Export CSV
                        </button>
                      </div>
                    </div>
                    {evaluationStatus === "error" ? (
                      <p className="mt-4 text-xs text-rose-300">
                        Οι μετρικές δεν είναι διαθέσιμες.
                      </p>
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
                                        className="w-1/2 rounded-t-sm bg-emerald-400/70"
                                        style={{
                                          height: `${Math.max(positiveRatio * 100, total ? 8 : 0)}%`,
                                        }}
                                      />
                                      <div
                                        className="w-1/2 rounded-t-sm bg-rose-400/70"
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
                        Πάτησε «Ανανέωση» για να φορτώσεις τα metrics.
                      </p>
                    )}
                  </div>
                )}
                {activeFocus === "audit" && (
                  <div className="mb-5 rounded-2xl border border-signal/30 bg-signal/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
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
                        <button
                          type="button"
                          onClick={() => void loadAuditEvents()}
                          className="rounded-lg border border-signal/30 px-3 py-1.5 text-xs text-signal"
                        >
                          {auditStatus === "loading" ? "Φόρτωση…" : "Ανανέωση"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void exportAudit()}
                          className="rounded-lg border border-border px-3 py-1.5 text-xs"
                        >
                          Export CSV
                        </button>
                      </div>
                    </div>
                    {auditStatus === "error" ? (
                      <p className="mt-4 text-xs text-rose-300">
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
                      <button
                        type="button"
                        onClick={() => void loadJobHistory()}
                        className="rounded-lg border border-primary/30 px-3 py-1.5 text-xs text-primary"
                      >
                        {jobHistoryStatus === "loading" ? "Φόρτωση…" : "Ανανέωση"}
                      </button>
                    </div>
                    {jobHistoryStatus === "error" ? (
                      <p className="mt-4 text-xs text-rose-300">
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
                                  <button
                                    type="button"
                                    onClick={() => void updateJob(job.id, "cancel")}
                                    className="text-rose-300 hover:underline"
                                  >
                                    Cancel
                                  </button>
                                )}
                                {job.status === "failed" && job.retryCount < 3 && (
                                  <button
                                    type="button"
                                    onClick={() => void updateJob(job.id, "retry")}
                                    className="text-primary hover:underline"
                                  >
                                    Retry
                                  </button>
                                )}
                              </div>
                            </div>
                            {job.lastError && (
                              <p className="mt-2 truncate text-[10px] text-rose-300">
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
                          Server-sent updates κάθε 3 δευτερόλεπτα.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void connectMissionStream()}
                        className="rounded-lg border border-primary/30 px-3 py-1.5 text-xs text-primary"
                      >
                        {liveStatus === "connected" ? "Live" : "Σύνδεση"}
                      </button>
                    </div>
                    <div className="mt-3 space-y-2">
                      {liveMissions.length === 0 && (
                        <p className="text-xs text-muted-foreground">
                          Δεν υπάρχουν missions ή δεν έχει συνδεθεί ακόμη το live stream.
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
                      <button
                        type="button"
                        onClick={() => void loadSystemStatus()}
                        className="rounded-lg border border-signal/30 px-3 py-1.5 text-xs text-signal hover:bg-signal/10"
                      >
                        Ανανέωση
                      </button>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="rounded-lg bg-card/70 p-2">
                        <p className="text-muted-foreground">Status</p>
                        <p className="mt-1 font-semibold text-ok">
                          {systemStatus?.status ?? "loading"}
                        </p>
                      </div>
                      <div className="rounded-lg bg-card/70 p-2">
                        <p className="text-muted-foreground">Missions</p>
                        <p className="mt-1 font-semibold">
                          {systemStatus?.counts?.missions ?? "—"}
                        </p>
                      </div>
                      <div className="rounded-lg bg-card/70 p-2">
                        <p className="text-muted-foreground">Tool runs</p>
                        <p className="mt-1 font-semibold">
                          {systemStatus?.counts?.toolRuns ?? "—"}
                        </p>
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
                      <button
                        type="button"
                        onClick={() => void loadApprovals()}
                        className="rounded-lg border border-warn/30 px-3 py-1.5 text-xs text-warn hover:bg-warn/10"
                      >
                        {approvalStatus === "loading" ? "Έλεγχος…" : "Ανανέωση"}
                      </button>
                    </div>
                    {approvalStatus === "error" && (
                      <p className="mt-3 text-xs text-destructive">
                        Η approval queue δεν είναι διαθέσιμη.
                      </p>
                    )}
                    {approvalStatus === "idle" && approvals.length === 0 && (
                      <p className="mt-3 text-xs text-muted-foreground">
                        Δεν υπάρχουν pending approvals.
                      </p>
                    )}
                    <div className="mt-3 space-y-2">
                      {approvals.map((approval) => (
                        <div
                          key={approval.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 bg-card/70 p-3"
                        >
                          <div>
                            <p className="font-mono text-xs text-foreground">{approval.tool}</p>
                            <p className="mt-1 text-[11px] text-muted-foreground">
                              Ζητήθηκε {new Date(approval.createdAt).toLocaleString("el-GR")}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => void resolveApproval(approval.id, "approved")}
                              className="rounded-md bg-ok/15 px-3 py-1.5 text-xs font-semibold text-ok"
                            >
                              Έγκριση
                            </button>
                            <button
                              type="button"
                              onClick={() => void resolveApproval(approval.id, "rejected")}
                              className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground"
                            >
                              Απόρριψη
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {[
                    { icon: Sparkles, label: "Ask brain", prompt: "Τι μπορείς να κάνεις;" },
                    { icon: Activity, label: "Missions", prompt: "Δείξε μου τα missions" },
                    { icon: ArrowUpRight, label: "Browser", prompt: "Έλεγξε τον browser operator" },
                    {
                      icon: ShieldCheck,
                      label: "System",
                      prompt: "Ποια είναι η κατάσταση του συστήματος;",
                    },
                  ].map(({ icon: Icon, label, prompt }) => (
                    <button
                      key={label}
                      type="button"
                      onClick={() => void send(prompt)}
                      disabled={isThinking}
                      className="group flex items-center gap-2 rounded-xl border border-border/70 bg-card/60 px-3 py-2.5 text-left text-xs transition-colors hover:border-primary/50 hover:bg-primary/8 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <Icon className="size-3.5 text-primary transition-transform group-hover:scale-110" />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
                <div className="flex flex-col gap-3">
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      className={`min-w-0 max-w-full rounded-2xl border p-4 text-sm leading-relaxed ${
                        m.role === "user"
                          ? "self-end whitespace-pre-wrap border-border bg-violet/15"
                          : m.error
                            ? "border-rose-400/40 bg-rose-400/5 text-rose-100"
                            : "border-border bg-card/80"
                      }`}
                    >
                      {m.role === "user" ? m.text : <ChatMarkdown text={m.text} />}
                      {m.error && m.retryText && (
                        <button
                          type="button"
                          onClick={() => void send(m.retryText, { retry: true })}
                          disabled={isThinking}
                          className="mt-3 inline-flex items-center gap-1 rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs font-semibold text-rose-200 hover:bg-rose-400/10 disabled:opacity-50"
                        >
                          <RotateCcw className="size-3" /> Ξαναδοκίμασε
                        </button>
                      )}
                      {m.role === "assistant" && m.id !== "welcome" && !m.error && (
                        <div className="mt-3 flex items-center gap-1 border-t border-border/60 pt-2">
                          <span className="mr-2 text-[10px] text-muted-foreground">
                            Αξιολόγηση απάντησης
                          </span>
                          <button
                            type="button"
                            onClick={() => void submitFeedback(m.id, "positive")}
                            aria-label="Χρήσιμη απάντηση"
                            className={`rounded-md p-1.5 transition-colors ${m.feedback === "positive" ? "bg-emerald-400/15 text-emerald-300" : "text-muted-foreground hover:bg-emerald-400/10 hover:text-emerald-300"}`}
                          >
                            <ThumbsUp className="size-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => void submitFeedback(m.id, "negative")}
                            aria-label="Μη χρήσιμη απάντηση"
                            className={`rounded-md p-1.5 transition-colors ${m.feedback === "negative" ? "bg-rose-400/15 text-rose-300" : "text-muted-foreground hover:bg-rose-400/10 hover:text-rose-300"}`}
                          >
                            <ThumbsDown className="size-3.5" />
                          </button>
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
                      onChange={(event) =>
                        setResearchMode(event.target.value as "auto" | "off" | "deep")
                      }
                      disabled={isThinking}
                      className="bg-transparent text-[10px] outline-none disabled:opacity-50"
                    >
                      <option value="auto">Research: Auto</option>
                      <option value="deep">Research: Deep</option>
                      <option value="off">Research: Off</option>
                    </select>
                  </label>
                </div>
                <button
                  type="button"
                  onClick={clearChat}
                  disabled={messages.length <= 1 && !conversationId}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Καθαρισμός συνομιλίας"
                >
                  <RotateCcw className="size-3" /> Καθαρισμός
                </button>
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
                <button
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
                  className={`inline-flex size-11 shrink-0 items-center justify-center rounded-xl border transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${isListening ? "border-rose-400/60 bg-rose-400/15 text-rose-300" : "border-border bg-background text-muted-foreground hover:border-primary hover:text-primary"}`}
                >
                  {isListening ? <MicOff className="size-4" /> : <Mic className="size-4" />}
                </button>
                <textarea
                  ref={chatInputRef}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
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
                <button
                  type="button"
                  onClick={() => {
                    setVoiceEnabled((enabled) => {
                      if (enabled) window.speechSynthesis?.cancel();
                      return !enabled;
                    });
                  }}
                  disabled={!voiceSupported}
                  aria-label={
                    voiceEnabled ? "Σίγασε τη φωνή του ΝΟΥΣ" : "Ενεργοποίησε τη φωνή του ΝΟΥΣ"
                  }
                  className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl border border-border bg-background text-muted-foreground hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {voiceEnabled ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
                </button>
                {isThinking ? (
                  <button
                    type="button"
                    onClick={stopChat}
                    className="inline-flex items-center gap-2 rounded-xl border border-rose-400/50 bg-rose-400/10 px-4 text-sm font-semibold text-rose-200"
                    aria-label="Διακοπή απάντησης"
                  >
                    <Square className="size-4" />
                    <span className="hidden sm:inline">Διακοπή</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => void send()}
                    disabled={!draft.trim()}
                    className="inline-flex items-center gap-2 rounded-xl bg-violet px-4 text-sm font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label="Στείλε μήνυμα"
                  >
                    <Send className="size-4" />
                    <span className="hidden sm:inline">Στείλε</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : section === "home" ? (
          <div className="min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
            <div className="min-w-0 max-w-full rounded-2xl border border-border bg-gradient-to-br from-violet/20 to-primary/10 p-5">
              <h1 className="font-display text-2xl font-bold">Καλώς ήρθες στον ΝΟΥΣ</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Agent chat + workspace + Android companion + deploy, σε μία οθόνη.
              </p>
            </div>

            <div className="mt-4 grid min-w-0 gap-4 lg:grid-cols-2">
              <Card title="System Snapshot">
                {tokenForm}
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

              <Card title="Missions">
                <MissionList missions={liveMissions} />
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
                <button
                  type="button"
                  onClick={() => void loadCompanionStatus()}
                  className="mt-3 rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
                >
                  Ανανέωση
                </button>
              </Card>
            </div>

            <div className="mt-4 rounded-2xl border border-violet/40 bg-violet/5 p-5">
              <h3 className="font-display text-base font-semibold">Τι θέλει να κάνει ο ΝΟΥΣ</h3>
              <p className="text-xs text-muted-foreground">
                Αυτόνομες προτάσεις — έγκρινε ή απόρριψε
              </p>
              {initiativesState === "error" && (
                <p className="mt-3 text-xs text-warn">
                  Δεν ήταν δυνατή η φόρτωση ή εκτέλεση των προτάσεων.
                </p>
              )}
              {initiatives.length === 0 ? (
                <div className="mt-4 rounded-xl border border-dashed border-border bg-card/50 p-4 text-sm text-muted-foreground">
                  {initiativesState === "loading"
                    ? "Φόρτωση…"
                    : "Δεν υπάρχουν εκκρεμείς προτάσεις."}
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
                        <p className="mt-1 text-xs text-muted-foreground">
                          {initiative.description}
                        </p>
                      )}
                      <div className="mt-2 flex gap-2">
                        <button
                          type="button"
                          disabled={!initiative.approve_route}
                          onClick={() => void resolveInitiative(initiative, "approve")}
                          className="rounded-lg bg-ok/15 px-3 py-1.5 text-xs font-semibold text-ok disabled:opacity-40"
                        >
                          Έγκριση
                        </button>
                        <button
                          type="button"
                          disabled={!initiative.reject_route}
                          onClick={() => void resolveInitiative(initiative, "reject")}
                          className="rounded-lg border border-border px-3 py-1.5 text-xs disabled:opacity-40"
                        >
                          Απόρριψη
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <button
                type="button"
                onClick={() => void loadInitiatives()}
                className="mt-3 rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
              >
                Ανανέωση προτάσεων
              </button>
            </div>
          </div>
        ) : (
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
                {section === "settings" && <div className="mt-5">{tokenForm}</div>}
                {sectionConfigs[section] && <SectionPanel section={section} />}
                {section === "documents" && (
                  <div className="mt-5 space-y-4">
                    <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-primary/40 bg-primary/5 p-8 text-center transition-colors hover:bg-primary/10">
                      <UploadCloud className="size-7 text-primary" />
                      <span className="mt-3 text-sm font-semibold">
                        Ανέβασε PDF, PNG, JPG, WEBP ή text
                      </span>
                      <span className="mt-1 text-xs text-muted-foreground">
                        Private storage · έως 15 MB · indexing και vision queue
                      </span>
                      <input
                        className="sr-only"
                        type="file"
                        accept="application/pdf,image/png,image/jpeg,image/webp,text/plain,text/markdown"
                        onChange={(event) => {
                          const file = event.target.files?.[0];
                          if (file) void uploadKnowledgeDocument(file);
                        }}
                      />
                    </label>
                    {knowledgeUpload !== "idle" && (
                      <p className="rounded-lg bg-background/70 p-3 text-xs text-muted-foreground">
                        {knowledgeUpload === "uploading"
                          ? "Ανεβαίνει και απομονώνεται…"
                          : knowledgeUpload === "indexed"
                            ? "Το αρχείο αποθηκεύτηκε και μπήκε στο knowledge index."
                            : "Το upload απέτυχε. Έλεγξε τύπο και μέγεθος αρχείου."}
                      </p>
                    )}
                    <button
                      type="button"
                      onClick={() => void loadKnowledgeDocuments()}
                      className="rounded-lg border border-border px-3 py-2 text-xs font-semibold"
                    >
                      Ανανέωση knowledge vault
                    </button>
                    <div className="space-y-2">
                      {knowledgeDocuments.map((document) => (
                        <div
                          key={document.id}
                          className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card/60 p-3"
                        >
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold">
                              {document.originalName}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {document.contentType} · {Math.ceil(document.sizeBytes / 1024)} KB
                            </p>
                          </div>
                          <span className="font-mono text-[10px] uppercase text-primary">
                            {document.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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
                            Ο NOUS μπορεί να χρησιμοποιεί model providers και repositories, αλλά
                            κάθε εξωτερική αλλαγή παραμένει proposal-first και απαιτεί ρητή έγκριση.
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
                          <button
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
                          </button>
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
                            Ελέγχει μόνο defensive controls του NOUS· δεν κάνει exploit ή scanning
                            τρίτων.
                          </p>
                        </div>
                        <button
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
                        </button>
                      </div>
                      {sentinelError && (
                        <p className="mt-3 text-xs text-rose-300">
                          Ο έλεγχος ασφαλείας δεν είναι διαθέσιμος αυτή τη στιγμή.
                        </p>
                      )}
                      {sentinel && (
                        <div className="mt-4 grid gap-3 md:grid-cols-[auto_1fr]">
                          <div className="flex size-20 flex-col items-center justify-center rounded-full border-4 border-primary/40">
                            <strong className="text-xl">{sentinel.score}</strong>
                            <span className="font-mono text-[9px] text-muted-foreground">
                              / 100
                            </span>
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
                        Read operations μπορούν να προταθούν αυτόματα. Commit, push, merge, delete
                        και external side effects δημιουργούν approval record, diff και audit event
                        πριν εκτελεστούν.
                      </p>
                    </div>
                  </div>
                )}
                <div className="mt-5 space-y-2">
                  {section === "missions" && <MissionList missions={liveMissions} />}
                </div>
              </Card>
              <Card title="Agent guardrails">
                <div className="space-y-3 text-sm">
                  {[
                    "Backend truth checks",
                    "Approval before side effects",
                    "Audit trail enabled",
                  ].map((item) => (
                    <div key={item} className="flex items-center gap-2">
                      <span className="size-2 rounded-full bg-ok" />
                      {item}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function NavButton({
  item,
  active,
  onClick,
}: {
  item: { icon: string; label: string };
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`my-0.5 flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors ${
        active
          ? "bg-violet/20 font-semibold text-foreground"
          : "text-muted-foreground hover:bg-violet/10 hover:text-foreground"
      }`}
    >
      <span className="w-5 text-center text-base">{item.icon}</span>
      {item.label}
    </button>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="min-w-0 max-w-full rounded-2xl border border-border bg-card p-5">
      <h3 className="mb-3 font-display text-base font-semibold">{title}</h3>
      {children}
    </section>
  );
}

function MissionList({
  missions,
}: {
  missions: Array<{ id: string; title: string; status: string }>;
}) {
  if (missions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Δεν υπάρχουν ενεργά missions στο live stream.</p>
    );
  }
  return (
    <>
      {missions.map((m) => (
        <div
          key={m.id}
          className="flex items-center justify-between gap-3 border-b border-border/60 py-2 text-sm last:border-0"
        >
          <span>{m.title}</span>
          <span
            className={`font-mono text-xs ${
              m.status === "running"
                ? "text-primary"
                : m.status === "done"
                  ? "text-ok"
                  : "text-warn"
            }`}
          >
            {m.status}
          </span>
        </div>
      ))}
    </>
  );
}

function StatBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  const safePct = Math.min(100, Math.max(0, pct));
  return (
    <div className="flex items-center gap-2 py-1 font-mono text-[11px] text-muted-foreground">
      <span className="w-8">{label}</span>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full ${color}`} style={{ width: `${safePct}%` }} />
      </div>
      <span>{safePct}%</span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card/60 p-2 text-center">
      <div className="font-mono text-sm text-foreground">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}
