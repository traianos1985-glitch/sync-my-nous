import { createFileRoute } from "@tanstack/react-router";
import { generateText, gateway } from "ai";
import { getModelCallMetrics, modelCallTimeoutMs, withTimeout } from "../lib/ai-observability";
import { getPersistentDailyBudget, recordPersistentModelCall } from "../lib/model-observability";
import { research, type ResearchMode } from "../lib/research-broker";
import { db } from "../lib/db";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { nousMessages } from "../lib/db/schema";
import { randomUUID } from "node:crypto";

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
  grounded = false,
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
        ...(grounded ? { tools: [{ google_search: {} }] } : {}),
      }),
      signal: AbortSignal.timeout(Math.min(modelCallTimeoutMs(), 20_000)),
    });
    if (!response.ok) return null;
    const data = (await response.json()) as {
      candidates?: Array<{
        content?: { parts?: Array<{ text?: string }> };
        groundingMetadata?: {
          groundingChunks?: Array<{ web?: { uri?: string; title?: string } }>;
        };
      }>;
    };
    const candidate = data.candidates?.[0];
    const answer = candidate?.content?.parts
      ?.map((part) => part.text ?? "")
      .join("")
      .trim();
    const citations = (candidate?.groundingMetadata?.groundingChunks ?? [])
      .map((chunk) => chunk.web)
      .filter((web): web is { uri: string; title?: string } => Boolean(web?.uri))
      .map((web) => ({
        title: web.title ?? web.uri,
        url: web.uri,
        domain: new URL(web.uri).hostname,
        sourceType: "google-grounded",
        retrievedAt: new Date().toISOString(),
      }));
    return answer
      ? { answer, model: grounded ? "gemini-2.5-flash-grounded" : "gemini-2.5-flash", citations }
      : null;
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

const requestWindows = new Map<string, number[]>();
function allowRequest(userId: string) {
  const now = Date.now();
  const recent = (requestWindows.get(userId) ?? []).filter((time) => now - time < 60_000);
  if (recent.length >= 20) return false;
  recent.push(now);
  requestWindows.set(userId, recent);
  return true;
}

function offlineAnswer(message: string) {
  const text = message.toLocaleLowerCase("el-GR");
  if (/(τι μπορείς|τι μπορεις|δυνατότητ|δυνατοτητ|can you)/.test(text)) {
    return "Μπορώ να συζητήσω, να αναλύσω απαιτήσεις, να σχεδιάσω λύσεις και να γράψω κώδικα στο workspace. Για πραγματική αναζήτηση στο διαδίκτυο, browser actions, missions ή αλλαγές στον υπολογιστή χρειάζεται να είναι συνδεδεμένο το αντίστοιχο NOUS backend εργαλείο. Αυτή τη στιγμή το AI chat λειτουργεί, αλλά δεν θα παρουσιάσω τις backend ενέργειες ως διαθέσιμες.";
  }
  return `Μπορ�� να σε βοηθήσω να το αναλύσουμε και να ετοιμάσουμε ασφαλές σχέδιο, αλλά το AI Gateway δεν απάντησε αυτή τη στιγμή. Δεν εκτέλεσα καμία εξωτερική ενέργεια. Δοκίμασε ξανά ή σύνδεσε το NOUS backend α�� ζητάς browser, missions ή αλλαγές αρχείων.`;
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
            researchMode?: ResearchMode;
            missionId?: string;
          };
          message = body.message?.trim() ?? "";
          const userId = await requireAuthenticatedUserId(request);
          if (!allowRequest(userId))
            return Response.json({ error: "Too many requests" }, { status: 429 });
          const missionId = body.missionId?.slice(0, 128);
          if (!message) {
            return Response.json({ error: "Το μήνυμα είναι κενό." }, { status: 400 });
          }

          const history = (body.history ?? []).slice(-10);
          try {
            await db.insert(nousMessages).values({
              id: randomUUID(),
              missionId: missionId ?? null,
              userId,
              role: "user",
              content: message,
              citations: [],
            });
          } catch (error) {
            console.warn(
              "[v0] message persistence unavailable",
              error instanceof Error ? error.message : error,
            );
          }
          const researchResult = await research(message, body.researchMode ?? "auto");
          const modelMessage = researchResult.context
            ? `${message}\n\n[READ-ONLY RESEARCH CONTEXT — cite only these sources and do not claim actions were performed]\n${researchResult.context}`
            : message;
          let budget;
          try {
            budget = await getPersistentDailyBudget(userId);
          } catch (error) {
            console.warn(
              "[v0] persistent budget unavailable",
              error instanceof Error ? error.message : error,
            );
            budget = {
              allowed: true,
              count: 0,
              limit: Number(process.env.NOUS_AI_DAILY_CALL_LIMIT ?? 100),
            };
          }
          if (!budget.allowed) {
            return Response.json(
              { ok: false, error: "Το ημερήσιο όριο του agent εξαντλήθηκε. Δοκίμασε ξανά αύριο." },
              { status: 429 },
            );
          }

          const saveAssistant = async (answer: string, citations = researchResult.citations) => {
            try {
              await db.insert(nousMessages).values({
                id: randomUUID(),
                missionId: missionId ?? null,
                userId,
                role: "assistant",
                content: answer,
                citations,
              });
            } catch (error) {
              console.warn(
                "[v0] assistant persistence unavailable",
                error instanceof Error ? error.message : error,
              );
            }
          };
          const startedAt = new Date().toISOString();
          const started = performance.now();
          if (researchResult.used || body.researchMode === "deep") {
            const grounded = await tryGeminiFallback(modelMessage, history, true);
            if (grounded) {
              await saveAssistant(grounded.answer, grounded.citations);
              return Response.json({
                ok: true,
                answer: grounded.answer,
                source: "gemini-google-search-grounded",
                model: grounded.model,
                citations: grounded.citations,
                researchUsed: true,
                mode: "connected",
              });
            }
          }
          try {
            const result = await withTimeout(
              generateText({
                model: gateway("openai/o4-mini"),
                system: SYSTEM_PROMPT,
                messages: [
                  ...history.map((item) => ({ role: item.role, content: item.text }) as const),
                  { role: "user" as const, content: modelMessage },
                ],
              }),
              modelCallTimeoutMs(),
            );
            await recordPersistentModelCall(
              {
                startedAt,
                durationMs: Math.round(performance.now() - started),
                ok: true,
                inputTokens: result.usage?.inputTokens,
                outputTokens: result.usage?.outputTokens,
                totalTokens: result.usage?.totalTokens,
              },
              userId,
              "vercel-ai-gateway",
              "openai/o4-mini",
            );
            await saveAssistant(result.text);
            return Response.json({
              ok: true,
              answer: result.text,
              source: "ai-gateway",
              citations: researchResult.citations,
              researchUsed: researchResult.used,
              mode: "connected",
            });
          } catch (error) {
            await recordPersistentModelCall(
              {
                startedAt,
                durationMs: Math.round(performance.now() - started),
                ok: false,
                error: error instanceof Error ? error.message : "unknown_error",
              },
              userId,
              "vercel-ai-gateway",
              "openai/o4-mini",
            );

            const groqFallback = await tryGroqFallback(modelMessage, history);
            if (groqFallback) {
              await saveAssistant(groqFallback.answer);
              return Response.json({
                ok: true,
                answer: groqFallback.answer,
                source: "groq-api",
                model: groqFallback.model,
                citations: researchResult.citations,
                researchUsed: researchResult.used,
                mode: "connected",
              });
            }

            const geminiFallback = await tryGeminiFallback(modelMessage, history);
            if (geminiFallback) {
              await saveAssistant(geminiFallback.answer);
              return Response.json({
                ok: true,
                answer: geminiFallback.answer,
                source: "gemini-api",
                model: geminiFallback.model,
                citations: researchResult.citations,
                researchUsed: researchResult.used,
                mode: "connected",
              });
            }

            const fallback = await tryOpenRouterFallback(modelMessage, history);
            if (fallback) {
              await saveAssistant(fallback.answer);
              return Response.json({
                ok: true,
                answer: fallback.answer,
                source: "openrouter-free-fallback",
                model: fallback.model,
                citations: researchResult.citations,
                researchUsed: researchResult.used,
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
