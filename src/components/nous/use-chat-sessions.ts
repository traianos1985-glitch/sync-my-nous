import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { initialChat, type ChatMessage } from "./dashboard-chat-model";
import {
  bootstrapSessions,
  createChatSession,
  sessionsStorageKey,
  type ChatSession,
} from "./chat-sessions-model";

export function useChatSessions(sessionId?: string) {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>(initialChat);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [chatLoaded, setChatLoaded] = useState(false);
  const [storageError, setStorageError] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    try {
      const stored = bootstrapSessions();
      const active = stored.find((s) => s.id === sessionId);
      setSessions(stored);
      if (!sessionId) {
        const first = stored[0];
        if (first)
          void navigate({ to: "/chat/$sessionId", params: { sessionId: first.id }, replace: true });
        return;
      }
      if (!active) {
        setStorageError("Η συνομιλία δεν υπάρχει σε αυτόν τον browser.");
        return;
      }
      setMessages(active.messages);
      setConversationId(active.conversationId);
      setDraft(active.draft);
      setChatLoaded(true);
    } catch {
      setStorageError("Το ιστορικό δεν μπορεί να αποθηκευτεί σε αυτόν τον browser.");
      setChatLoaded(true);
    }
  }, [sessionId, navigate]);

  useEffect(() => {
    if (!chatLoaded || !sessionId) return;
    setSessions((current) => {
      const next = current.map((s) =>
        s.id === sessionId
          ? { ...s, messages, conversationId, draft, updatedAt: new Date().toISOString() }
          : s,
      );
      try {
        window.localStorage.setItem(sessionsStorageKey, JSON.stringify(next));
      } catch {
        setStorageError(
          "Το ιστορικό δεν αποθηκεύτηκε: ο χώρος του browser είναι γεμάτος ή μη διαθέσιμος.",
        );
      }
      return next;
    });
  }, [messages, conversationId, draft, chatLoaded, sessionId]);

  const selectSession = (id: string) => {
    setHistoryOpen(false);
    void navigate({ to: "/chat/$sessionId", params: { sessionId: id } });
  };
  const newSession = () => {
    const session = createChatSession(crypto.randomUUID());
    const next = [...sessions, session];
    try {
      window.localStorage.setItem(sessionsStorageKey, JSON.stringify(next));
    } catch {
      setStorageError("Δεν είναι δυνατή η αποθήκευση νέας συνομιλίας.");
      return;
    }
    setSessions(next);
    selectSession(session.id);
  };
  const renameSession = (id: string, title: string) => {
    if (!title.trim()) return;
    setSessions((current) => {
      const next = current.map((s) =>
        s.id === id ? { ...s, title: title.trim().slice(0, 120) } : s,
      );
      try {
        window.localStorage.setItem(sessionsStorageKey, JSON.stringify(next));
      } catch {
        setStorageError("Η μετονομασία δεν αποθηκεύτηκε.");
      }
      return next;
    });
  };
  return {
    sessions,
    sessionId,
    messages,
    setMessages,
    draft,
    setDraft,
    conversationId,
    setConversationId,
    chatLoaded,
    setChatLoaded,
    storageError,
    historyOpen,
    setHistoryOpen,
    selectSession,
    newSession,
    renameSession,
  };
}
