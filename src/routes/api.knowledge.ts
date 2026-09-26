import { createFileRoute } from "@tanstack/react-router";
import { put } from "@vercel/blob";
import { createHash, randomUUID } from "node:crypto";
import { and, desc, eq } from "drizzle-orm";
import { db } from "../lib/db";
import { nousKnowledgeChunks, nousKnowledgeDocuments } from "../lib/db/schema";
import { validateUploadMetadata } from "../lib/content-security";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

const MAX_FILE_BYTES = 15 * 1024 * 1024;
const allowedTypes = new Set([
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
  "text/plain",
  "text/markdown",
]);

function extractText(bytes: Uint8Array, contentType: string) {
  if (contentType.startsWith("text/")) return new TextDecoder().decode(bytes).slice(0, 200_000);
  if (contentType === "application/pdf") {
    return new TextDecoder("latin1")
      .decode(bytes)
      .replace(/\\([^()]*)\\/g, "$1")
      .replace(/[^\\x20-\\x7E\\n]+/g, " ")
      .slice(0, 200_000);
  }
  return "Image uploaded. Vision extraction is queued for the NOUS knowledge worker.";
}

function chunks(text: string) {
  const size = 4_000;
  return Array.from({ length: Math.ceil(text.length / size) }, (_, index) =>
    text.slice(index * size, (index + 1) * size),
  ).filter(Boolean);
}

export const Route = createFileRoute("/api/knowledge")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const documents = await db
          .select()
          .from(nousKnowledgeDocuments)
          .where(eq(nousKnowledgeDocuments.userId, userId))
          .orderBy(desc(nousKnowledgeDocuments.createdAt))
          .limit(50);
        return Response.json({ ok: true, documents });
      },
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const form = await request.formData();
        const file = form.get("file");
        if (!(file instanceof File))
          return Response.json({ error: "file is required" }, { status: 400 });
        if (file.size > MAX_FILE_BYTES || !allowedTypes.has(file.type))
          return Response.json({ error: "Unsupported or oversized file" }, { status: 415 });
        const safe = validateUploadMetadata(file.name, file.size, file.type);
        if (!safe.ok) return Response.json({ error: safe.reason }, { status: 400 });
        const bytes = new Uint8Array(await file.arrayBuffer());
        const sha256 = createHash("sha256").update(bytes).digest("hex");
        const id = randomUUID();
        const originalName = file.name.trim().slice(0, 180);
        const blob = await put(
          `knowledge/${userId}/${id}-${originalName}`,
          new Blob([bytes], { type: file.type }),
          { access: "private", addRandomSuffix: false },
        );
        const extractedText = extractText(bytes, file.type);
        await db.insert(nousKnowledgeDocuments).values({
          id,
          userId,
          pathname: blob.pathname,
          originalName,
          contentType: file.type,
          sizeBytes: file.size,
          sha256,
          status: file.type.startsWith("image/") ? "vision_queued" : "indexed",
          extractedText,
        });
        const rows = chunks(extractedText).map((content, chunkIndex) => ({
          id: randomUUID(),
          documentId: id,
          userId,
          chunkIndex,
          content,
          embeddingStatus: "pending",
        }));
        if (rows.length) await db.insert(nousKnowledgeChunks).values(rows);
        return Response.json(
          {
            ok: true,
            document: {
              id,
              name: safe.filename,
              contentType: file.type,
              status: file.type.startsWith("image/") ? "vision_queued" : "indexed",
              chunks: rows.length,
            },
          },
          { status: 201 },
        );
      },
    },
  },
});
