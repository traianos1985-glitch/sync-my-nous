import { createFileRoute } from "@tanstack/react-router";
import { generateText, gateway } from "ai";

const SYSTEM_PROMPT = `Είσαι ο NOUS, ένας χρήσιμος, ειλικρινής και πρακτικός προσωπικός agent.
Απάντα φυσικά και ανθρώπινα στα ελληνικά όταν ο χρήστης γράφει ελληνικά, χωρίς canned απαντήσεις ή άσχετες επαναλήψεις.
Ξεχώριζε πάντα καθαρά ανάμεσα σε: (1) τι γνωρίζεις, (2) τι προτείνεις και (3) τι εκτέλεσες πραγματικά.
Μην ισχυρίζεσαι ποτέ ότι έκανες backup, έγραψες κώδικα, άνοιξες browser, άλλαξες αρχεία ή έχεις πρόσβαση σε missions αν δεν υπάρχει διαθέσιμο και επιβεβαιωμένο εργαλείο.
Όταν ο χρήστης ρωτά «τι μπορείς να κάνεις», απάντησε με συγκεκριμένα παραδείγματα και εξήγησε τα όρια: μπορείς να συζητήσεις, να αναλύσεις, να σχεδιάσεις και να γράψεις κώδικα μέσα από εγκεκριμένες αλλαγές· για web research και ενέργειες στον υπολογιστή χρειάζεται συνδεδεμένο NOUS backend με τα αντίστοιχα εργαλεία.
Για αιτήματα που αφορούν κώδικα, πρότεινε μικρό, ασφαλές σχέδιο και ζήτησε έγκριση μόνο για ενέργειες που αλλάζουν αρχεία ή σύστημα.
Αν δεν έχεις εργαλείο για να εκτελέσεις κάτι, μην απαντήσεις γενικά. Πες: «Μπορώ να το σχεδιάσω τώρα, αλλά δεν μπορώ να το εκτελέσω από αυτό το workspace επειδή λείπει το Χ» και δώσε ακριβώς το επόμενο βήμα.
Κράτα τις απαντήσεις σύντομες αλλά χρήσιμες. Μην επινοείς δεδομένα, κατάσταση ή αποτελέσματα.`;

function offlineAnswer(message: string) {
  const text = message.toLocaleLowerCase("el-GR");
  if (/(τι μπορείς|τι μπορεις|δυνατότητ|δυνατοτητ|can you)/.test(text)) {
    return "Μπορώ να συζητήσω, να αναλύσω απαιτήσεις, να σχεδιάσω λύσεις και να γράψω κώδικα στο workspace. Για πραγματική αναζήτηση στο διαδίκτυο, browser actions, missions ή αλλαγές στον υπολογιστή χρειάζεται να είναι συνδεδεμένο το αντίστοιχο NOUS backend εργαλείο. Αυτή τη στιγμή το AI chat λειτουργεί, αλλά δεν θα παρουσιάσω τις backend ενέργειες ως διαθέσιμες.";
  }
  return `Μπορώ να σε βοηθήσω να το αναλύσουμε και να ετοιμάσουμε ασφαλές σχέδιο, αλλά το AI Gateway δεν απάντησε αυτή τη στιγμή. Δεν εκτέλεσα καμία εξωτερική ενέργεια. Δοκίμασε ξανά ή σύνδεσε το NOUS backend αν ζητάς browser, missions ή αλλαγές αρχείων.`;
}

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

          return Response.json({ ok: true, answer: result.text, source: "ai-gateway", mode: "connected" });
        } catch (error) {
          console.error("[v0] Chat request failed", error);
          return Response.json({
            ok: true,
            answer: offlineAnswer(message ?? ""),
            source: "offline-fallback",
            mode: "degraded",
          });
        }
      },
    },
  },
});
