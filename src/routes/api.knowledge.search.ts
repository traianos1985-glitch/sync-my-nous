import { createFileRoute } from "@tanstack/react-router";
import { and, eq, sql } from "drizzle-orm";
import { embedKnowledgeChunks } from "../lib/knowledge-processor";
import { db } from "../lib/db";
import { nousKnowledgeChunks } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/knowledge/search")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json().catch(() => ({}))) as { query?: string; limit?: number };
        const query = body.query?.trim().slice(0, 2_000);
        if (!query) return Response.json({ error: "query is required" }, { status: 400 });
        const queryEmbedding = (await embedKnowledgeChunks([query]))[0];
        const limit = Math.min(Math.max(body.limit ?? 5, 1), 20);
        const vector = `[${queryEmbedding.join(",")}]`;
        const chunks = await db
          .select({
            id: nousKnowledgeChunks.id,
            documentId: nousKnowledgeChunks.documentId,
            chunkIndex: nousKnowledgeChunks.chunkIndex,
            content: nousKnowledgeChunks.content,
            score: sql<number>`1 - (${nousKnowledgeChunks.embeddingVector} <=> ${vector}::vector)`,
          })
          .from(nousKnowledgeChunks)
          .where(
            and(
              eq(nousKnowledgeChunks.userId, userId),
              eq(nousKnowledgeChunks.embeddingStatus, "ready"),
              sql`${nousKnowledgeChunks.embeddingVector} IS NOT NULL`,
            ),
          )
          .orderBy(sql`${nousKnowledgeChunks.embeddingVector} <=> ${vector}::vector`)
          .limit(limit);
        const results = chunks.filter((chunk) => chunk.score > 0.2);
        return Response.json({ ok: true, query, results, model: "google/gemini-embedding-2" });
      },
    },
  },
});
