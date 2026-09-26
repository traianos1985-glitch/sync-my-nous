import { createFileRoute } from "@tanstack/react-router";
import { generateText, gateway } from "ai";

const SYSTEM_PROMPT = `Είσαι ο NOUS, ένας χρήσιμος και ειλικρινής προσωπικός agent.
Απάντα φυσικά, ανθρώπινα και συγκεκριμένα στα ελληνικά όταν ο χρήστης γράφει ελληνικά.
Μην ισχυρίζεσαι ότι εκτέλεσες ενέργειες στον υπολογιστή, ότι έκανες backup ή ότι έχεις πρόσβαση σε missions αν δεν υπάρχει πραγματικό εργαλείο που το επιβεβαιώνει.
Αν δεν γνωρίζεις κάτι, πες το καθαρά. Μπορείς να εξηγείς τι μπορείς να κάνεις, να προτείνεις βήματα και να βοηθάς στον προγραμματισμό εφαρμογών.
Κράτα τις απαντήσεις σύντομες αλλά χρήσιμες και κάνε διευκρινιστική ερώτηση μόνο όταν είναι απαραίτητη.`;

export const Route = createFileRoute("/api/chat")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        try {
          const body = (await request.json()) as {
            message?: string;
            history?: Array<{ role: "user" | "assistant"; text: string }>;
          };
          const message = body.message?.trim();
          if (!message) {
            return Response.json({ error: "Το μήνυμα είναι κενό." }, { status: 400 });
          }

          const history = (body.history ?? []).slice(-10);
          const result = await generateText({
            model: gateway("openai/o4-mini"),
            system: SYSTEM_PROMPT,
            messages: [
              ...history.map((item) => ({ role: item.role, content: item.text }) as const),
              { role: "user" as const, content: message },
            ],
          });

          return Response.json({ ok: true, answer: result.text, source: "ai-gateway" });
        } catch (error) {
          console.error("[v0] Chat request failed", error);
          return Response.json(
            { error: "Δεν μπόρεσα να συνδεθώ με το AI Gateway. Έλεγξε ότι το service είναι διαθέσιμο." },
            { status: 502 },
          );
        }
      },
    },
  },
});
