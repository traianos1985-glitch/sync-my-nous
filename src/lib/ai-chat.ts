import { createServerFn } from "@tanstack/react-start";
import { streamText, type ModelMessage } from "ai";

type ChatInput = {
  messages: { role: "user" | "assistant"; content: string }[];
  model?: string;
  context?: string;
};

const SYSTEM = `Είσαι ο "ΝΟΥΣ" (NOUS AI OS), ένας αυτόνομος AI agent που λειτουργεί σαν λειτουργικό σύστημα.
Λειτουργείς σε "Owner Mode" για τον διαχειριστή σου.
Απαντάς πάντα στα Ελληνικά, με σαφήνεια, τεχνική ακρίβεια και πρακτικό τόνο.
Μπορείς να βοηθήσεις με: goals, missions, μνήμη & αποφάσεις, app builder, έγγραφα, scheduler, backups, self-healing και έλεγχο συστήματος.
Όταν ο χρήστης ζητά μια ενέργεια στο σύστημα, εξήγησε σύντομα τι θα κάνεις και ζήτα επιβεβαίωση αν είναι μη αναστρέψιμη.
Κράτα τις απαντήσεις εστιασμένες· απόφυγε περιττή φλυαρία.`;

export const chatStream = createServerFn({ method: "POST" })
  .validator((input: ChatInput) => {
    if (!input || !Array.isArray(input.messages)) {
      throw new Error("messages array required");
    }
    return {
      messages: input.messages.slice(-20).map((m) => ({
        role: m.role,
        content: String(m.content ?? "").slice(0, 8000),
      })),
      model: input.model,
      context: input.context ? String(input.context).slice(0, 4000) : undefined,
    };
  })
  .handler(async ({ data }) => {
    const system = data.context ? `${SYSTEM}\n\nΤρέχον context συστήματος:\n${data.context}` : SYSTEM;

    const result = streamText({
      model: data.model || "anthropic/claude-sonnet-4.5",
      system,
      messages: data.messages as ModelMessage[],
    });

    return result.toTextStreamResponse();
  });
