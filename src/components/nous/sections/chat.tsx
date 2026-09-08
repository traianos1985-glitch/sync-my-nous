import { useEffect, useRef, useState } from "react";
import { Send, Sparkles, Trash2, Loader2 } from "lucide-react";
import { chatStream } from "@/lib/ai-chat";
import { actions, useNous } from "@/lib/store";
import { Badge } from "@/components/nous/ui";

const SUGGESTIONS = [
  "Τι missions τρέχουν αυτή τη στιγμή;",
  "Πρότεινε 3 βελτιώσεις για το service.",
  "Φτιάξε πλάνο για μετάβαση σε βάση δεδομένων.",
  "Σύνοψη της κατάστασης του συστήματος.",
];

export function ChatSection() {
  const { chat, settings, missions, goals, documents } = useNous();
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [chat]);

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    setDraft("");
    setBusy(true);

    const context = [
      `Missions: ${missions.length} (${missions.filter((m) => m.status === "running").length} running).`,
      `Goals: ${goals.length} (${goals.filter((g) => g.status === "active").length} active).`,
      `Έγγραφα στη μνήμη: ${documents.length}.`,
    ].join(" ");

    const payload = [
      ...chat.map((m) => ({ role: m.role, content: m.text })),
      { role: "user" as const, content: message },
    ];

    actions.addChatMessage("user", message);
    const assistant = actions.addChatMessage("assistant", "");

    try {
      const res = (await chatStream({
        data: { messages: payload, model: settings.model, context },
      })) as unknown as Response;

      if (!res.body) throw new Error("no stream");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        actions.updateChatMessage(assistant.id, acc);
      }
      if (!acc.trim()) {
        actions.updateChatMessage(assistant.id, "(Κενή απάντηση από το μοντέλο.)");
      }
    } catch (err) {
      console.log("[v0] chat error:", err);
      actions.updateChatMessage(
        assistant.id,
        "Σφάλμα σύνδεσης με το μοντέλο. Δοκίμασε ξανά σε λίγο.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          {chat.map((m) => (
            <div
              key={m.id}
              className={`max-w-[90%] whitespace-pre-wrap rounded-2xl border border-border px-4 py-3 text-sm leading-relaxed ${
                m.role === "user"
                  ? "self-end border-violet/40 bg-violet/15"
                  : "self-start bg-card/80"
              }`}
            >
              {m.text || (
                <span className="inline-flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="size-3.5 animate-spin" /> σκέφτομαι…
                </span>
              )}
            </div>
          ))}

          {chat.length <= 1 && (
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="flex items-center gap-2 rounded-xl border border-border bg-card/60 px-3 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
                >
                  <Sparkles className="size-3.5 shrink-0 text-primary" />
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-border bg-card/60 p-4">
        <div className="mx-auto max-w-3xl">
          <div className="mb-2 flex items-center justify-between">
            <Badge tone="primary">
              <Sparkles className="size-3" />
              {settings.model.split("/")[1] ?? settings.model}
            </Badge>
            <button
              onClick={() => actions.clearChat()}
              className="inline-flex items-center gap-1 font-mono text-[11px] text-muted-foreground transition-colors hover:text-destructive"
            >
              <Trash2 className="size-3" /> καθάρισμα
            </button>
          </div>
          <div className="flex gap-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) {
                  e.preventDefault();
                  send(draft);
                }
              }}
              rows={2}
              placeholder="Γράψε στον ΝΟΥΣ…  (Enter για αποστολή, Shift+Enter για νέα γραμμή)"
              className="flex-1 resize-none rounded-xl border border-input bg-background p-3 text-sm outline-none focus:border-primary"
            />
            <button
              onClick={() => send(draft)}
              disabled={busy || !draft.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-violet px-4 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              <span className="hidden sm:inline">{busy ? "…" : "Στείλε"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
