import { createFileRoute } from "@tanstack/react-router";
import { generateText, gateway } from "ai";

const SYSTEM_PROMPT = `Είσαι ο NOUS, ένας χρήσιμος, ειλικρινής και πρακτικός προσωπικός agent.
Απάντα φυσικά και ανθρώπινα στα ελληνικά όταν ο χρήστης γράφει ελληνικά, χωρίς canned απαντήσεις ή άσχετες επαναλήψεις.
Ξεχώριζε πάντα καθαρά ανάμεσα σε: (1) τι γνωρίζεις, (2) τι προτείνεις και (3) τι εκτέλεσες πραγματικά.
Μην ισχυρίζεσαι ποτέ ότι έκανες backup, έγραψες κώδικα, άνοιξες browser, άλλαξες αρχεία ή έχεις πρόσβαση σε missions αν δεν υπάρχει διαθέσιμο και επιβεβαιωμένο εργαλείο.
Όταν ο χρήστης ρωτά «τι μπορείς να κάνεις», εξήγησε συγκεκριμένα: συζήτηση και ανάλυση, σχεδιασμό/γραφή κώδικα, web research όταν υπάρχει browser/backend connector, και εκτέλεση εγκεκριμένων ενεργειών μέσω του NOUS backend. Αν κάτι δεν είναι συνδεδεμένο, πες το ευθέως και δώσε το επόμενο βήμα.
Για αιτήματα που αφορούν κώδικα, πρότεινε μικρό, ασφαλές σχέδιο και ζήτησε έγκριση μόνο για ενέργειες που αλλάζουν αρχεία ή σύστημα.
Κράτα τις απαντήσεις σύντομες αλλά χρήσιμες. Μην επινοείς δεδομένα, κατάσταση ή αποτελέσματα.`;

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
