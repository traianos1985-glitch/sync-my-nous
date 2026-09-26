import { createFileRoute } from "@tanstack/react-router";
import { get } from "@vercel/blob";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { and, eq } from "drizzle-orm";
import { db } from "../lib/db";
import { nousKnowledgeDocuments } from "../lib/db/schema";

export const Route = createFileRoute("/api/knowledge/file")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = requireAuthenticatedUserId(request);
        const pathname = new URL(request.url).searchParams.get("pathname");
        if (!pathname) return Response.json({ error: "pathname is required" }, { status: 400 });
        const [document] = await db
          .select()
          .from(nousKnowledgeDocuments)
          .where(
            and(
              eq(nousKnowledgeDocuments.userId, userId),
              eq(nousKnowledgeDocuments.pathname, pathname),
            ),
          )
          .limit(1);
        if (!document) return Response.json({ error: "Not found" }, { status: 404 });
        const result = await get(document.pathname, {
          access: "private",
          ifNoneMatch: request.headers.get("if-none-match") ?? undefined,
        });
        if (!result) return new Response("Not found", { status: 404 });
        if (result.statusCode === 304)
          return new Response(null, {
            status: 304,
            headers: { ETag: result.blob.etag, "Cache-Control": "private, no-cache" },
          });
        return new Response(result.stream, {
          headers: {
            "Content-Type": result.blob.contentType,
            ETag: result.blob.etag,
            "Cache-Control": "private, no-cache",
            "Content-Disposition": `inline; filename="${document.originalName.replace(/["\\\r\n]/g, "_")}"`,
          },
        });
      },
    },
  },
});
