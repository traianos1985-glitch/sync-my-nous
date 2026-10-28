export type Citation = {
  title: string;
  url: string;
  domain: string;
  sourceType?: string;
  retrievedAt?: string;
};

type SpeechRecognitionEventLike = Event & {
  results: { length: number; [index: number]: { [index: number]: { transcript: string } } };
};
export type SpeechRecognitionLike = {
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
export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  feedback?: "positive" | "negative";
  error?: boolean;
  retryText?: string;
};

export const chatStorageKey = "nous-chat-v1";
export const maxStoredChatMessages = 80;
const maxStoredMessageCharacters = 12_000;
const maxStoredCitations = 8;

export function normalizeStoredChatMessage(value: unknown): ChatMessage | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const candidate = value as Record<string, unknown>;
  if (
    typeof candidate["id"] !== "string" ||
    !candidate["id"].trim() ||
    candidate["id"].length > 128 ||
    (candidate["role"] !== "user" && candidate["role"] !== "assistant") ||
    typeof candidate["text"] !== "string"
  ) {
    return null;
  }

  const citations = Array.isArray(candidate["citations"])
    ? candidate["citations"]
        .filter(
          (item): item is Citation =>
            Boolean(item) &&
            typeof item === "object" &&
            typeof (item as Citation).title === "string" &&
            typeof (item as Citation).url === "string" &&
            /^https?:\/\//i.test((item as Citation).url) &&
            typeof (item as Citation).domain === "string",
        )
        .slice(0, maxStoredCitations)
        .map((item) => ({
          title: item.title.slice(0, 300),
          url: item.url.slice(0, 2_000),
          domain: item.domain.slice(0, 255),
          ...(typeof item.sourceType === "string"
            ? { sourceType: item.sourceType.slice(0, 80) }
            : {}),
          ...(typeof item.retrievedAt === "string"
            ? { retrievedAt: item.retrievedAt.slice(0, 80) }
            : {}),
        }))
    : undefined;

  return {
    id: candidate["id"],
    role: candidate["role"],
    text: candidate["text"].slice(0, maxStoredMessageCharacters),
    ...(citations?.length ? { citations } : {}),
    ...(candidate["feedback"] === "positive" || candidate["feedback"] === "negative"
      ? { feedback: candidate["feedback"] }
      : {}),
    ...(candidate["error"] === true ? { error: true } : {}),
    ...(typeof candidate["retryText"] === "string"
      ? { retryText: candidate["retryText"].slice(0, maxStoredMessageCharacters) }
      : {}),
  };
}

export function normalizeConversationId(value: unknown): string | null {
  return typeof value === "string" && /^[0-9]{1,30}$/.test(value) ? value : null;
}

export function loadStoredChat(): {
  messages: ChatMessage[];
  conversationId: string | null;
} | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(chatStorageKey);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    const stored = parsed as Record<string, unknown>;
    const messages = Array.isArray(stored["messages"])
      ? stored["messages"]
          .map(normalizeStoredChatMessage)
          .filter((message): message is ChatMessage => message !== null)
          .slice(-maxStoredChatMessages)
      : [];
    if (messages.length === 0) return null;
    return {
      messages,
      conversationId: normalizeConversationId(stored["conversationId"]),
    };
  } catch {
    return null;
  }
}

export function sourcesToCitations(sources: unknown): Citation[] {
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

export const initialChat: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    text: "Καλώς ήρθες. Είμαι ο NOUS. Μπορώ να συζητήσω φυσικά, να αναλύσω στόχους, να προτείνω βήματα και —όταν είναι συνδεδεμένο το backend— να εκτελέσ�� εγκεκριμένες ενέργειες. Δεν θα παρουσιάσω ποτέ μια πρόταση ως ολοκληρωμένη ενέργεια χωρίς επιβεβαίωση.",
  },
];

export function exportChatAsMarkdown(
  messages: ChatMessage[],
  conversationId?: string | null,
): string {
  const date = new Date().toISOString().slice(0, 19).replace("T", " ");
  let md = `# NOUS Chat Export\n\n`;
  md += `- **Ημερομηνία:** ${date}\n`;
  if (conversationId) {
    md += `- **ID Συνομιλίας:** ${conversationId}\n`;
  }
  md += `- **Σύνολο μηνυμάτων:** ${messages.length}\n\n---\n\n`;

  for (const message of messages) {
    const roleLabel = message.role === "user" ? "Χρήστης" : "NOUS";
    md += `### ${roleLabel}\n\n${message.text}\n\n`;
    if (message.citations?.length) {
      md += `*Πηγές:*\n`;
      for (const citation of message.citations) {
        md += `- [${citation.title}](${citation.url}) (${citation.domain})\n`;
      }
      md += `\n`;
    }
    md += `---\n\n`;
  }
  return md;
}

export function exportChatAsJson(messages: ChatMessage[], conversationId?: string | null): string {
  return JSON.stringify(
    {
      exportedAt: new Date().toISOString(),
      conversationId: conversationId ?? null,
      messageCount: messages.length,
      messages: messages.map((m) => ({
        id: m.id,
        role: m.role,
        text: m.text,
        citations: m.citations,
        feedback: m.feedback,
      })),
    },
    null,
    2,
  );
}

export function downloadChatFile(content: string, filename: string, mimeType: string): void {
  if (typeof window === "undefined") return;
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
