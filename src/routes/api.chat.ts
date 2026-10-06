import { createFileRoute } from "@tanstack/react-router";
import { getModelCallMetrics, modelCallTimeoutMs } from "../lib/ai-observability";
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
Για αιτήματα που αφορούν κώδικα, πρότεινε μικρό, ασφαλές σχέδιο και ζήτησε έγκριση μόνο για ενέργειες που αλλάζουν αρχεία ή σύστημα.
Κράτα τις απαντήσεις σύντομες αλλά χρήσιμες. Μην επινοείς δεδομένα, κατάσταση ή αποτελέσματα.`;

const GEMINI_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

type ChatHistory = Array<{ role: "user" | "assistant"; text: string }>;

type GeminiResult = {
  answer: string;
  model: string;
  citations: Array<{
    title: string;
    url: string;
    domain: string;
    sourceType: "google-grounded";
    retrievedAt: string;
  }>;
};

async function callGemini(
  message: string,
  history: ChatHistory,
  grounded = false,
): Promise<GeminiResult | null> {
  const apiKey = process.env["GEMINI_API_KEY"] ?? process.env["GCP_API_KEY"];
  if (!apiKey) return null;

  try {
    const response = await fetch(`${GEMINI_URL}?key=${encodeURIComponent(apiKey)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [
          ...history.map((item) => ({
            role: item.role === "assistant" ? "model" : "user",
            parts: [{ text: item.text }],
          })),
          { role: "user", parts: [{ text: message }] },
        ],
        generationConfig: { temperature: 0.3, maxOutputTokens: 1600 },
        ...(grounded ? { tools: [{ google_search: {} }] } : {}),
      }),
      signal: AbortSignal.timeout(Math.min(modelCallTimeoutMs(), 20_000)),
    });
    if (!response.ok) return null;

    const data = (await response.json()) as {
      candidates?: Array<{
        content?: { parts?: Array<{ text?: string }> };
        groundingMetadata?: { groundingChunks?: Array<{ web?: { uri?: string; title?: string } }> };
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
        sourceType: "google-grounded" as const,
        retrievedAt: new Date().toISOString(),
      }));

    return answer
      ? { answer, model: grounded ? "gemini-2.5-flash-grounded" : "gemini-2.5-flash", citations }
      : null;
  } catch {
    return null;
  }
}

const requestWindows = new Map<string, number[]>();
function allowRequest(userId: string): boolean {
  const now = Date.now();
  const recent = (requestWindows.get(userId) ?? []).filter((time) => now - time < 60_000);
  if (recent.length >= 20) return false;
  recent.push(now);
  requestWindows.set(userId, recent);
  return true;
}

export const Route = createFileRoute("/api/chat")({
  server: {
    handlers: {
      GET: async () => Response.json(getModelCallMetrics()),
      POST: async ({ request }) => {
        let userId = "";
        let message = "";
        try {
          const body = (await request.json()) as {
            message?: string;
            history?: ChatHistory;
            researchMode?: ResearchMode;
            missionId?: string;
          };
          message = body.message?.trim() ?? "";
          userId = await requireAuthenticatedUserId(request);
          if (!allowRequest(userId))
            return Response.json({ ok: false, error: "Too many requests" }, { status: 429 });
          if (!message)
            return Response.json({ ok: false, error: "Το μήνυμα είναι κενό." }, { status: 400 });

          const history = (body.history ?? []).slice(-10);
          await db.insert(nousMessages).values({
            id: randomUUID(),
            missionId: body.missionId?.slice(0, 128) ?? null,
            userId,
            role: "user",
            content: message,
            citations: [],
          });

          const researchResult = await research(message, body.researchMode ?? "auto");
          const modelMessage = researchResult.context
            ? `${message}\n\n[READ-ONLY RESEARCH CONTEXT — cite only these sources]\n${researchResult.context}`
            : message;
          const budget = await getPersistentDailyBudget(userId);
          if (!budget.allowed) {
            return Response.json(
              { ok: false, error: "Το ημερήσιο όριο του agent εξαντλήθηκε. Δοκίμασε ξανά αύριο." },
              { status: 429 },
            );
          }

          const startedAt = new Date().toISOString();
          const started = performance.now();
          const gemini = await callGemini(
            modelMessage,
            history,
            researchResult.used || body.researchMode === "deep",
          );
          if (!gemini) throw new Error("Gemini did not respond");

          await recordPersistentModelCall(
            { startedAt, durationMs: Math.round(performance.now() - started), ok: true },
            userId,
            "gemini-api",
            gemini.model,
          );
          await db.insert(nousMessages).values({
            id: randomUUID(),
            missionId: body.missionId?.slice(0, 128) ?? null,
            userId,
            role: "assistant",
            content: gemini.answer,
            citations: researchResult.used ? gemini.citations : [],
          });
          return Response.json({
            ok: true,
            answer: gemini.answer,
            source: "gemini-api",
            model: gemini.model,
            citations: researchResult.used ? gemini.citations : researchResult.citations,
            researchUsed: researchResult.used,
            mode: "connected",
          });
        } catch (error) {
          if (userId) {
            try {
              await recordPersistentModelCall(
                {
                  startedAt: new Date().toISOString(),
                  durationMs: 0,
                  ok: false,
                  error: error instanceof Error ? error.message : "unknown_error",
                },
                userId,
                "gemini-api",
                "gemini-2.5-flash",
              );
            } catch {
              // Metrics are best-effort when the model request fails.
            }
          }
          console.error("[nous] Chat request failed", error);
          return Response.json({ ok: false, error: "AI service unavailable" }, { status: 503 });
        }
      },
    },
  },
});
