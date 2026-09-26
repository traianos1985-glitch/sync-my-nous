import { createFileRoute } from "@tanstack/react-router";
import { and, eq } from "drizzle-orm";
import { embedKnowledgeChunks, cosineSimilarity } from "../lib/knowledge-processor";
import { db } from "../lib/db";
import { nousKnowledgeChunks } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/knowledge/search")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = requireAuthenticatedUserId(request);
        const body = (await request.json().catch(() => ({}))) as { query?: string; limit?: number };
        const query = body.query?.trim().slice(0, 2_000);
        if (!query) return Response.json({ error: "query is required" }, { status: 400 });
        const queryEmbedding = (await embedKnowledgeChunks([query]))[0];
        const chunks = await db
          .select()
          .from(nousKnowledgeChunks)
          .where(
            and(
              eq(nousKnowledgeChunks.userId, userId),
              eq(nousKnowledgeChunks.embeddingStatus, "ready"),
            ),
          );
        const results = chunks
          .map((chunk) => ({
            ...chunk,
            score: cosineSimilarity(queryEmbedding, (chunk.embedding as number[]) ?? []),
          }))
          .filter((chunk) => chunk.score > 0.2)
          .sort((left, right) => right.score - left.score)
          .slice(0, Math.min(Math.max(body.limit ?? 5, 1), 20))
          .map(({ embedding: _embedding, ...chunk }) => chunk);
        return Response.json({ ok: true, query, results, model: "google/gemini-embedding-2" });
      },
    },
  },
});
