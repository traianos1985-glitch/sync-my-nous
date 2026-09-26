import { createFileRoute } from "@tanstack/react-router";
import { and, eq } from "drizzle-orm";
import { db } from "../lib/db";
import { nousKnowledgeChunks, nousKnowledgeDocuments } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { embedKnowledgeChunks } from "../lib/knowledge-processor";

export const Route = createFileRoute("/api/knowledge/process")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json().catch(() => ({}))) as { documentId?: string };
        if (!body.documentId)
          return Response.json({ error: "documentId is required" }, { status: 400 });
        const document = (
          await db
            .select()
            .from(nousKnowledgeDocuments)
            .where(
              and(
                eq(nousKnowledgeDocuments.id, body.documentId),
                eq(nousKnowledgeDocuments.userId, userId),
              ),
            )
            .limit(1)
        )[0];
        if (!document) return Response.json({ error: "Document not found" }, { status: 404 });
        const claimed = await db
          .update(nousKnowledgeDocuments)
          .set({ status: "processing", updatedAt: new Date() })
          .where(
            and(
              eq(nousKnowledgeDocuments.id, document.id),
              eq(nousKnowledgeDocuments.userId, userId),
              eq(nousKnowledgeDocuments.status, "extraction_review"),
            ),
          )
          .returning({ id: nousKnowledgeDocuments.id });
        if (!claimed.length)
          return Response.json(
            { ok: true, documentId: document.id, status: document.status },
            { status: 202 },
          );
        const chunks = await db
          .select()
          .from(nousKnowledgeChunks)
          .where(
            and(
              eq(nousKnowledgeChunks.documentId, document.id),
              eq(nousKnowledgeChunks.userId, userId),
            ),
          );
        const pendingChunks = chunks.filter((chunk) => chunk.embeddingStatus !== "ready");
        const embeddings = await embedKnowledgeChunks(pendingChunks.map((chunk) => chunk.content));
        for (let index = 0; index < pendingChunks.length; index += 1) {
          await db
            .update(nousKnowledgeChunks)
            .set({
              embedding: embeddings[index],
              embeddingVector: embeddings[index],
              embeddingStatus: "ready",
            })
            .where(
              and(
                eq(nousKnowledgeChunks.id, pendingChunks[index].id),
                eq(nousKnowledgeChunks.userId, userId),
              ),
            );
        }
        await db
          .update(nousKnowledgeDocuments)
          .set({ status: "indexed", updatedAt: new Date() })
          .where(
            and(
              eq(nousKnowledgeDocuments.id, document.id),
              eq(nousKnowledgeDocuments.userId, userId),
            ),
          );
        return Response.json({
          ok: true,
          documentId: document.id,
          embeddedChunks: embeddings.length,
          model: "google/gemini-embedding-2",
        });
      },
    },
  },
});
