export type BrowserDriverStatus = {
  time?: number;
  ready: boolean;
  node_ready: boolean;
  capabilities?: {
    time?: number;
    commands?: Record<string, boolean>;
    browser_driver_ready?: boolean;
    node_ready?: boolean;
    deploy_ready?: boolean;
    install_hints?: Record<string, string>;
  };
  supported_when_ready?: string[];
};

export type BrowserBridgeStatus = {
  mode?: string;
  pending?: number;
  done?: number;
  jobs?: BrowserBridgeJob[];
  time?: number;
};

export type BrowserBridgeJob = {
  id: string;
  url?: string;
  reason?: string;
  status?: "pending" | "running" | "completed" | "failed" | string;
  actions?: Array<{ type: string; selector?: string; value?: string }>;
  created_at?: number | string;
  result?: Record<string, unknown>;
};

export type BrowserSearchResult = {
  ok: boolean;
  query?: string;
  answer?: string;
  result?: string;
  raw?: unknown;
  source?: string;
  error?: string;
};

export type BrowserReadResult = {
  ok: boolean;
  url?: string;
  result?:
    | string
    | {
        title?: string;
        text?: string;
        content?: string;
        links?: string[];
        summary?: string;
        source?: string;
        word_count?: number;
      };
  error?: string;
};

export type BrowserActionType = "open" | "click" | "fill" | "screenshot" | "wait";

export type BrowserActionItem = {
  id: string;
  type: BrowserActionType;
  selector?: string;
  value?: string;
  description?: string;
};

export type WebPreset = {
  label: string;
  url: string;
  category: "docs" | "news" | "api" | "bench";
  description: string;
};

export const DEFAULT_WEB_PRESETS: WebPreset[] = [
  {
    label: "Hacker News Top",
    url: "https://news.ycombinator.com",
    category: "news",
    description: "Τεχνολογικές ειδήσεις και συζητήσεις",
  },
  {
    label: "MDN Web Docs",
    url: "https://developer.mozilla.org/en-US/docs/Web/API",
    category: "docs",
    description: "Επίσημα Web APIs & standards",
  },
  {
    label: "GitHub Trending",
    url: "https://github.com/trending",
    category: "news",
    description: "Δημοφιλή open-source repositories",
  },
  {
    label: "ArXiv AI Papers",
    url: "https://arxiv.org/list/cs.AI/recent",
    category: "docs",
    description: "Πρόσφατα papers τεχνητής νοημοσύνης",
  },
  {
    label: "JSONPlaceholder API",
    url: "https://jsonplaceholder.typicode.com/posts/1",
    category: "api",
    description: "Δημόσιο test REST endpoint",
  },
];

export function sanitizeTargetUrl(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) return "";
  if (/^javascript:/i.test(trimmed)) return "";
  if (!/^https?:\/\//i.test(trimmed)) {
    return `https://${trimmed}`;
  }
  return trimmed;
}

export function cleanSearchQuery(query: string): string {
  return query
    .trim()
    .replace(/^(?:ψάξε|ψαξε|αναζήτησε|αναζητησε|search|find)\s+/i, "")
    .replace(/^(?:για|for|στο\s+διαδίκτυο|online)\s+/i, "")
    .trim();
}

export function formatJobStatus(status?: string): {
  label: string;
  tone: "green" | "yellow" | "blue" | "red" | "muted";
} {
  const norm = (status || "").toLowerCase();
  switch (norm) {
    case "completed":
    case "done":
    case "success":
      return { label: "Ολοκληρώθηκε", tone: "green" };
    case "running":
    case "active":
      return { label: "Εκτελείται", tone: "blue" };
    case "pending":
    case "queued":
      return { label: "Σε αναμονή", tone: "yellow" };
    case "failed":
    case "error":
      return { label: "Απέτυχε", tone: "red" };
    default:
      return { label: norm || "Άγνωστο", tone: "muted" };
  }
}

export function createDefaultActions(targetUrl = "https://example.com"): BrowserActionItem[] {
  return [
    {
      id: "act-1",
      type: "open",
      value: targetUrl,
      description: "Πλοήγηση στην αρχική διεύθυνση",
    },
    {
      id: "act-2",
      type: "screenshot",
      description: "Λήψη στιγμιότυπου οθόνης",
    },
  ];
}

export function extractReadText(content: BrowserReadResult["result"]): string {
  if (!content) return "";
  if (typeof content === "string") return content;
  if (content.content) return content.content;
  if (content.text) return content.text;
  if (content.summary) return content.summary;
  return JSON.stringify(content, null, 2);
}

export function estimateWordCount(text: string): number {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(Boolean).length;
}
