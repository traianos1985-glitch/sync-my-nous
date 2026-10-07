import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { geminiModelCandidates, shouldTryGeminiFallback } from "../lib/gemini-models";
import { db } from "../lib/db";
import { nousMessages } from "../lib/db/schema";
import { randomUUID } from "node:crypto";

const GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models";

const SYSTEM_PROMPT = `Είσαι ο NOUS, ένας χρήσιμος, ειλικρινής και πρακτικός προσωπικός agent.
Απάντα φυσικά και ανθρώπινα στα ελληνικά όταν ο χρήστης γράφει ελληνικά.
Μην επινοείς δεδομένα, ενέργειες ή αποτελέσματα που δεν επιβεβαιώθηκαν.
Όταν ο χρήστης ζητά ενέργεια στο σύστημα, ξεχώρισε καθαρά: (1) τι κατάλαβες, (2) τι μπορείς να κάνεις, (3) τι χρειάζεται έγκριση και (4) τι ολοκληρώθηκε πραγματικά.
Αν δεν έχεις πρόσβαση σε εργαλείο ή δεδομένο, πες το ρητά και πρότεινε το ασφαλέστερο επόμενο βήμα.`;

type ChatMessage = { role: "user" | "assistant"; text?: string; content?: string };

type GeminiChunk = {
  candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
};

function parseGeminiChunk(line: string): string {
  if (!line.startsWith("data: ")) return "";
  try {
    const chunk = JSON.parse(line.slice(6)) as GeminiChunk;
    return chunk.candidates?.[0]?.content?.parts?.map((part) => part.text ?? "").join("") ?? "";
  } catch {
    return "";
  }
}

export const Route = createFileRoute("/api/chat/stream")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as {
          message?: string;
          history?: ChatMessage[];
          missionId?: string;
          activeFocus?: string;
          researchMode?: "auto" | "off" | "deep";
        };
        const message = body.message?.trim().slice(0, 20_000) ?? "";
        if (!message) return Response.json({ error: "Το μήνυμα είναι κενό." }, { status: 400 });

        const apiKey = process.env["GEMINI_API_KEY"] ?? process.env["GCP_API_KEY"];
        if (!apiKey)
          return Response.json({ ok: false, error: "AI service unavailable" }, { status: 503 });

        const focusContext = [
          body.activeFocus ? `Ενεργό workspace: ${body.activeFocus}.` : "",
          body.researchMode && body.researchMode !== "auto"
            ? `Research mode: ${body.researchMode}.`
            : "",
        ]
          .filter(Boolean)
          .join(" ");
        const contents = [
          ...(focusContext
            ? [{ role: "user" as const, parts: [{ text: `System context: ${focusContext}` }] }]
            : []),
          ...(body.history ?? []).slice(-10).flatMap((item) => {
            const text = (item.text ?? item.content ?? "").trim();
            return text
              ? [
                  {
                    role: item.role === "assistant" ? ("model" as const) : ("user" as const),
                    parts: [{ text }],
                  },
                ]
              : [];
          }),
          { role: "user", parts: [{ text: message }] },
        ];

        let response: Response | null = null;
        const models = geminiModelCandidates();
        for (const [index, model] of models.entries()) {
          try {
            response = await fetch(
              `${GEMINI_API_BASE}/${model}:streamGenerateContent?alt=sse&key=${encodeURIComponent(apiKey)}`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
                body: JSON.stringify({
                  systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
                  contents,
                  generationConfig: { temperature: 0.3, maxOutputTokens: 1600 },
                }),
                signal: AbortSignal.timeout(30_000),
              },
            );
            if (response.ok && response.body) break;
            if (index < models.length - 1 && shouldTryGeminiFallback(response.status)) continue;
            return Response.json(
              { ok: false, error: "Το AI service δεν είναι διαθέσιμο αυτή τη στιγμή." },
              { status: 503 },
            );
          } catch {
            if (index === models.length - 1)
              return Response.json(
                { ok: false, error: "Το AI service δεν είναι διαθέσιμο αυτή τη στιγμή." },
                { status: 503 },
              );
          }
        }

        if (!response?.ok || !response.body) {
          return Response.json(
            { ok: false, error: "Το AI service δεν είναι διαθέσιμο αυτή τη στιγμή." },
            { status: 503 },
          );
        }

        const encoder = new TextEncoder();
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const stream = new ReadableStream({
          async start(controller) {
            let buffer = "";
            let answer = "";
            const send = (event: string, data: unknown) => {
              controller.enqueue(
                encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`),
              );
            };

            send("start", { ok: true });
            try {
              while (true) {
                const { value, done } = await reader.read();
                buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";
                for (const line of lines) {
                  const text = parseGeminiChunk(line.trim());
                  if (text) {
                    answer += text;
                    send("token", { text });
                  }
                }
                if (done) break;
              }

              if (!answer) throw new Error("Gemini returned an empty response");
              await db.insert(nousMessages).values({
                id: randomUUID(),
                missionId: body.missionId?.slice(0, 128) ?? null,
                userId,
                role: "assistant",
                content: answer,
                citations: [],
              });
              send("done", { ok: true });
              controller.close();
            } catch {
              send("error", { ok: false, error: "AI service unavailable" });
              controller.close();
            }
          },
        });

        return new Response(stream, {
          headers: {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-cache, no-store",
            Connection: "keep-alive",
            "X-Accel-Buffering": "no",
          },
        });
      },
    },
  },
});
