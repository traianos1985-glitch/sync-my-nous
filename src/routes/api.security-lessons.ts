import { createFileRoute } from "@tanstack/react-router";
import { and, desc, eq } from "drizzle-orm";
import { createHash, randomUUID } from "node:crypto";
import { db } from "../lib/db";
import { nousSecurityLessons } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";

export const Route = createFileRoute("/api/security-lessons")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const lessons = await db
          .select()
          .from(nousSecurityLessons)
          .where(eq(nousSecurityLessons.userId, userId))
          .orderBy(desc(nousSecurityLessons.createdAt))
          .limit(100);
        return Response.json({ ok: true, lessons });
      },
      POST: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const body = (await request.json()) as {
          category?: string;
          severity?: string;
          title?: string;
          lesson?: string;
          remediation?: string;
          sourceEvent?: string;
        };
        const values = [
          body.category,
          body.severity,
          body.title,
          body.lesson,
          body.remediation,
          body.sourceEvent,
        ].map((value) => value?.trim().slice(0, 4000));
        if (values.some((value) => !value))
          return Response.json({ error: "All lesson fields are required" }, { status: 400 });
        const [category, severity, title, lesson, remediation, sourceEvent] = values as string[];
        const fingerprint = createHash("sha256")
          .update(`${category}:${title}:${lesson}`)
          .digest("hex");
        const [created] = await db
          .insert(nousSecurityLessons)
          .values({
            id: randomUUID(),
            userId,
            fingerprint,
            category,
            severity,
            title,
            lesson,
            remediation,
            sourceEvent,
          })
          .onConflictDoNothing({
            target: [nousSecurityLessons.userId, nousSecurityLessons.fingerprint],
          })
          .returning();
        if (created) return Response.json({ ok: true, lesson: created }, { status: 201 });
        const [existing] = await db
          .select()
          .from(nousSecurityLessons)
          .where(
            and(
              eq(nousSecurityLessons.userId, userId),
              eq(nousSecurityLessons.fingerprint, fingerprint),
            ),
          )
          .limit(1);
        return Response.json({ ok: true, lesson: existing, deduplicated: true });
      },
    },
  },
});
