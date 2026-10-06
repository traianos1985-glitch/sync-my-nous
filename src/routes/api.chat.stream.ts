import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { db } from "../lib/db";
import { nousMessages } from "../lib/db/schema";
import { randomUUID } from "node:crypto";

const GEMINI_STREAM_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent";

const SYSTEM_PROMPT = `Είσαι ο NOUS, ένας χρήσιμος, ειλικρινής και πρακτικός προσωπικός agent.
Απάντα φυσικά και ανθρώπινα στα ελληνικά όταν ο χρήστης γράφει ελληνικά.
Μην επινοείς δεδομένα, ενέργειες ή αποτελέσματα που δεν επιβεβαιώθηκαν.`;

type ChatMessage = { role: "user" | "assistant"; text: string };

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
        };
        const message = body.message?.trim().slice(0, 20_000) ?? "";
        if (!message) return Response.json({ error: "Το μήνυμα είναι κενό." }, { status: 400 });

        const apiKey = process.env["GEMINI_API_KEY"] ?? process.env["GCP_API_KEY"];
        if (!apiKey)
          return Response.json({ ok: false, error: "AI service unavailable" }, { status: 503 });

        const contents = [
          ...(body.history ?? []).slice(-10).map((item) => ({
            role: item.role === "assistant" ? "model" : "user",
            parts: [{ text: item.text }],
          })),
          { role: "user", parts: [{ text: message }] },
        ];

        let response: Response;
        try {
          response = await fetch(`${GEMINI_STREAM_URL}?alt=sse&key=${encodeURIComponent(apiKey)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
            body: JSON.stringify({
              systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
              contents,
              generationConfig: { temperature: 0.3, maxOutputTokens: 1600 },
            }),
            signal: AbortSignal.timeout(30_000),
          });
        } catch {
          return Response.json({ ok: false, error: "AI service unavailable" }, { status: 503 });
        }

        if (!response.ok || !response.body) {
          return Response.json({ ok: false, error: "AI service unavailable" }, { status: 503 });
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
