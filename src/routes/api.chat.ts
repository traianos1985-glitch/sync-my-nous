import { createFileRoute } from "@tanstack/react-router";
import { generateText, gateway } from "ai";
import {
  canStartModelCall,
  getModelCallMetrics,
  modelCallTimeoutMs,
  recordModelCall,
  withTimeout,
} from "../lib/ai-observability";

const SYSTEM_PROMPT = `Είσαι ο NOUS, ένας χρήσιμος, ειλικρινής και πρακτικός προσωπικός agent.
Απάντα φυσικά και ανθρώπινα στα ελληνικά όταν ο χρήστης γράφει ελληνικά, χωρίς canned απαντήσεις ή άσχετες επαναλήψεις.
Ξεχώριζε πάντα καθαρά ανάμεσα σε: (1) τι γνωρίζεις, (2) τι προτείνεις και (3) τι εκτέλεσες πραγματικά.
Μην ισχυρίζεσαι ποτέ ότι έκανες backup, έγραψες κώδικα, άνοιξες browser, άλλαξες αρχεία ή έχεις πρόσβαση σε missions αν δεν υπάρχει διαθέσιμο και επιβεβαιωμένο εργαλείο.
Όταν ο χρήστης ρωτά «τι μπορείς να κάνεις», απάντησε με συγκεκριμένα παραδείγματα και εξήγησε τα όρια: μπορείς να συζητήσεις, να αναλύσεις, να σχεδιάσεις και να γράψεις κώδικα μέσα από εγκεκριμένες αλλαγές· για web research και ενέργειες στον υπολογιστή χρειάζεται συνδεδεμένο NOUS backend με τα αντίστοιχα εργαλεία.
Για αιτήματα που αφορούν κώδικα, πρότεινε μικρό, ασφαλές σχέδιο και ζήτησε έγκριση μόνο για ενέργειες που αλλάζουν αρχεία ή σύστημα.
Αν δεν έχεις εργαλείο για να εκτελέσεις κάτι, μην απαντήσεις γενικά. Πες: «Μπορώ να το σχεδιάσω τώρα, αλλά δεν μπορώ να το εκτελέσω από αυτό το workspace επειδή λείπει το Χ» και δώσε ακριβώς το επόμενο βήμα.
Κράτα τις απαντήσεις σύντομες αλλά χρήσιμες. Μην επινοείς δεδομένα, κατάσταση ή αποτελέσματα.`;

const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";
const GROQ_MODEL = "openai/gpt-oss-120b";

async function tryGroqFallback(
  message: string,
  history: Array<{ role: "user" | "assistant"; text: string }>,
) {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) return null;

  try {
    const response = await fetch(GROQ_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          ...history.map((item) => ({ role: item.role, content: item.text })),
          { role: "user", content: message },
        ],
        temperature: 0.3,
        max_tokens: 1600,
      }),
      signal: AbortSignal.timeout(Math.min(modelCallTimeoutMs(), 20_000)),
    });
    if (!response.ok) return null;
    const data = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const answer = data.choices?.[0]?.message?.content?.trim();
    return answer ? { answer, model: GROQ_MODEL } : null;
  } catch {
    return null;
  }
}

const GEMINI_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

async function tryGeminiFallback(
  message: string,
  history: Array<{ role: "user" | "assistant"; text: string }>,
) {
  const apiKey = process.env.GCP_API_KEY;
  if (!apiKey) return null;

  try {
    const contents = [
      ...history.map((item) => ({
        role: item.role === "assistant" ? "model" : "user",
        parts: [{ text: item.text }],
      })),
      { role: "user", parts: [{ text: message }] },
    ];
    const response = await fetch(`${GEMINI_URL}?key=${encodeURIComponent(apiKey)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents,
        generationConfig: { temperature: 0.3, maxOutputTokens: 1600 },
      }),
      signal: AbortSignal.timeout(Math.min(modelCallTimeoutMs(), 20_000)),
    });
    if (!response.ok) return null;
    const data = (await response.json()) as {
      candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
    };
    const answer = data.candidates?.[0]?.content?.parts
      ?.map((part) => part.text ?? "")
      .join("")
      .trim();
    return answer ? { answer, model: "gemini-2.5-flash" } : null;
  } catch {
    return null;
  }
}

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const OPENROUTER_FREE_MODELS = [
  "qwen/qwen3-coder:free",
  "deepseek/deepseek-r1-0528:free",
  "google/gemma-3-27b-it:free",
];

async function tryOpenRouterFallback(
  message: string,
  history: Array<{ role: "user" | "assistant"; text: string }>,
) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) return null;

  for (const model of OPENROUTER_FREE_MODELS) {
    try {
      const response = await fetch(OPENROUTER_URL, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://nous.local",
          "X-Title": "NOUS-AI-OS",
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: "system", content: SYSTEM_PROMPT },
            ...history.map((item) => ({ role: item.role, content: item.text })),
            { role: "user", content: message },
          ],
          temperature: 0.3,
          max_tokens: 1600,
        }),
        signal: AbortSignal.timeout(Math.min(modelCallTimeoutMs(), 20_000)),
      });
      if (!response.ok) continue;
      const data = (await response.json()) as {
        choices?: Array<{ message?: { content?: string } }>;
      };
      const answer = data.choices?.[0]?.message?.content?.trim();
      if (answer) return { answer, model };
    } catch {
      // Try the next free model, then use the deterministic offline response.
    }
  }
  return null;
}

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
      GET: async () => Response.json(getModelCallMetrics()),
      POST: async ({ request }) => {
        let message = "";
        try {
          const body = (await request.json()) as {
            message?: string;
            history?: Array<{ role: "user" | "assistant"; text: string }>;
          };
          message = body.message?.trim() ?? "";
          if (!message) {
            return Response.json({ error: "Το μήνυμα είναι κενό." }, { status: 400 });
          }

          const history = (body.history ?? []).slice(-10);
          const budget = canStartModelCall();
          if (!budget.allowed) {
            return Response.json(
              { ok: false, error: "Το ημερήσιο όριο του agent εξαντλήθηκε. Δοκίμασε ξανά αύριο." },
              { status: 429 },
            );
          }

          const startedAt = new Date().toISOString();
          const started = performance.now();
          try {
            const result = await withTimeout(
              generateText({
                model: gateway("openai/o4-mini"),
                system: SYSTEM_PROMPT,
                messages: [
                  ...history.map((item) => ({ role: item.role, content: item.text }) as const),
                  { role: "user" as const, content: message },
                ],
              }),
              modelCallTimeoutMs(),
            );
            recordModelCall({
              startedAt,
              durationMs: Math.round(performance.now() - started),
              ok: true,
              inputTokens: result.usage?.inputTokens,
              outputTokens: result.usage?.outputTokens,
              totalTokens: result.usage?.totalTokens,
            });
            return Response.json({
              ok: true,
              answer: result.text,
              source: "ai-gateway",
              mode: "connected",
            });
          } catch (error) {
            recordModelCall({
              startedAt,
              durationMs: Math.round(performance.now() - started),
              ok: false,
              error: error instanceof Error ? error.message : "unknown_error",
            });

            const groqFallback = await tryGroqFallback(message, history);
            if (groqFallback) {
              return Response.json({
                ok: true,
                answer: groqFallback.answer,
                source: "groq-api",
                model: groqFallback.model,
                mode: "connected",
              });
            }

            const geminiFallback = await tryGeminiFallback(message, history);
            if (geminiFallback) {
              return Response.json({
                ok: true,
                answer: geminiFallback.answer,
                source: "gemini-api",
                model: geminiFallback.model,
                mode: "connected",
              });
            }

            const fallback = await tryOpenRouterFallback(message, history);
            if (fallback) {
              return Response.json({
                ok: true,
                answer: fallback.answer,
                source: "openrouter-free-fallback",
                model: fallback.model,
                mode: "connected",
              });
            }
            throw error;
          }
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
