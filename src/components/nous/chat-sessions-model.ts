import {
  initialChat,
  loadStoredChat,
  normalizeStoredChatMessage,
  normalizeConversationId,
  maxStoredChatMessages,
  type ChatMessage,
} from "./dashboard-chat-model";

export type ChatSession = {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
  conversationId: string | null;
  draft: string;
};
export const sessionsStorageKey = "nous-chat-sessions-v1";

export function normalizeSessions(value: unknown): ChatSession[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  return value.flatMap((item): ChatSession[] => {
    if (
      !item ||
      typeof item !== "object" ||
      typeof item.id !== "string" ||
      !/^[a-zA-Z0-9-]{1,128}$/.test(item.id) ||
      seen.has(item.id)
    )
      return [];
    seen.add(item.id);
    return [
      {
        id: item.id,
        title: typeof item.title === "string" ? item.title.slice(0, 120) : "Νέα συνομιλία",
        updatedAt: typeof item.updatedAt === "string" ? item.updatedAt : "",
        messages: Array.isArray(item.messages)
          ? item.messages
              .map(normalizeStoredChatMessage)
              .filter((m: ChatMessage | null): m is ChatMessage => m !== null)
              .slice(-maxStoredChatMessages)
          : initialChat,
        conversationId: normalizeConversationId(item.conversationId),
        draft: typeof item.draft === "string" ? item.draft.slice(0, 12000) : "",
      },
    ];
  });
}

export function createChatSession(id: string): ChatSession {
  return {
    id,
    title: "Νέα συνομιλία",
    updatedAt: new Date().toISOString(),
    messages: initialChat,
    conversationId: null,
    draft: "",
  };
}

export function searchSessions(sessions: ChatSession[], query: string): ChatSession[] {
  const needle = query.trim().toLocaleLowerCase();
  return sessions
    .filter(
      (s) =>
        !needle ||
        `${s.title} ${s.messages.map((m) => m.text).join(" ")}`
          .toLocaleLowerCase()
          .includes(needle),
    )
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function bootstrapSessions(): ChatSession[] {
  const raw = window.localStorage.getItem(sessionsStorageKey);
  const sessions = raw ? normalizeSessions(JSON.parse(raw)) : [];
  if (sessions.length) return sessions;
  const legacy = loadStoredChat();
  const session = createChatSession(crypto.randomUUID());
  if (legacy) {
    session.messages = legacy.messages;
    session.conversationId = legacy.conversationId;
    session.title =
      legacy.messages.find((m) => m.role === "user")?.text.slice(0, 80) || session.title;
  }
  window.localStorage.setItem(sessionsStorageKey, JSON.stringify([session]));
  return [session];
}
