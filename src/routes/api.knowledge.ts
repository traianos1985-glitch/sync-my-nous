import { createFileRoute } from "@tanstack/react-router";
import { put } from "@vercel/blob";
import { createHash, randomUUID } from "node:crypto";
import { and, desc, eq, sql } from "drizzle-orm";
import { db } from "lib/db";
import {
  nousKnowledgeChunks,
  nousKnowledgeDocuments,
  nousObservabilityEvents,
} from "../lib/db/schema";
import { validateUploadMetadata } from "../lib/content-security";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { scanUpload, shouldReleaseFromQuarantine } from "../lib/quarantine-scanner";
import { createJob } from "../lib/db/jobs";
import { isDatabaseRateLimited } from "../lib/security";

const MAX_FILE_BYTES = 15 * 1024 * 1024;
const allowedTypes = new Set([
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
  "text/plain",
  "text/markdown",
]);

function hasExpectedFileSignature(bytes: Uint8Array, contentType: string) {
  if (contentType === "application/pdf")
    return new TextDecoder().decode(bytes.slice(0, 5)) === "%PDF-";
  if (contentType === "image/png")
    return bytes
      .slice(0, 8)
      .every((value, index) => value === [137, 80, 78, 71, 13, 10, 26, 10][index]);
  if (contentType === "image/jpeg")
    return bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
  if (contentType === "image/webp")
    return (
      new TextDecoder().decode(bytes.slice(0, 4)) === "RIFF" &&
      new TextDecoder().decode(bytes.slice(8, 12)) === "WEBP"
    );
  return true;
}

function extractText(bytes: Uint8Array, contentType: string) {
  if (contentType.startsWith("text/")) return new TextDecoder().decode(bytes).slice(0, 200_000);
  if (contentType === "application/pdf") {
    const raw = new TextDecoder("latin1").decode(bytes);
    const textStrings: string[] = [];
    let inText = false;
    let current = "";
    for (let i = 0; i < raw.length; i++) {
      const ch = raw.charCodeAt(i);
      if (ch === 0x28) {
        inText = true;
        current = "";
      } else if (ch === 0x29 && inText) {
        if (current.trim()) textStrings.push(current);
        inText = false;
      } else if (inText) {
        if (ch >= 0x20 && ch <= 0x7e) current += raw[i];
        else if (ch === 0x0a || ch === 0x0d) current += "\n";
        else current += " ";
      }
    }
    return textStrings.join("\n").slice(0, 200_000);
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
        if (await isDatabaseRateLimited(request, db as never, sql, "knowledge-upload"))
          return Response.json(
            { error: "Upload rate limit exceeded" },
            { status: 429, headers: { "Retry-After": "60" } },
          );
        const form = await request.formData();
        const file = form.get("file");
        if (!(file instanceof File))
          return Response.json({ error: "file is required" }, { status: 400 });
        if (file.size > MAX_FILE_BYTES || !allowedTypes.has(file.type))
          return Response.json({ error: "Unsupported or oversized file" }, { status: 415 });
        const safe = validateUploadMetadata(file.name, file.size, file.type);
        if (!safe.ok) return Response.json({ error: safe.reason }, { status: 400 });
        const bytes = new Uint8Array(await file.arrayBuffer());
        if (!hasExpectedFileSignature(bytes, file.type))
          return Response.json(
            { error: "File signature does not match declared type" },
            { status: 415 },
          );
        const scan = scanUpload(bytes, file.type);
        const id = randomUUID();
        const sha256 = createHash("sha256").update(bytes).digest("hex");
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
          status:
            !scan.clean || file.type.startsWith("image/") ? "quarantined" : "extraction_review",
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
        const job = await createJob(userId, "knowledge.ingest", {
          documentId: id,
          scan,
          releaseEligible: shouldReleaseFromQuarantine(file.type, scan),
        });
        await db.insert(nousObservabilityEvents).values({
          id: randomUUID(),
          userId,
          event: "knowledge.upload.quarantine_scan",
          metadata: {
            documentId: id,
            jobId: job.id,
            clean: scan.clean,
            signatures: scan.signatures,
          },
        });
        return Response.json(
          {
            ok: true,
            document: {
              id,
              name: file.name,
              contentType: file.type,
              status:
                !scan.clean || file.type.startsWith("image/") ? "quarantined" : "extraction_review",
              chunks: rows.length,
              jobId: job.id,
              scan: { clean: scan.clean, reason: scan.reason },
            },
          },
          { status: 201 },
        );
      },
    },
  },
});
