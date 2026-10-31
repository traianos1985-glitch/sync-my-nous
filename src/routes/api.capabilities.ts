import { createFileRoute } from "@tanstack/react-router";
import { asc, eq, or, isNull } from "drizzle-orm";
import { db } from "../lib/db";
import { nousRuntimeCapabilities } from "../lib/db/schema";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { toolDefinitions } from "../lib/tool-registry";

const registeredCapabilities = Object.entries(toolDefinitions).map(([name, definition]) => ({
  name,
  description: definition.description,
  risk: definition.risk,
  enabled: true,
  source: "web-runtime",
}));

export const Route = createFileRoute("/api/capabilities")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const capabilities = await db
          .select({
            name: nousRuntimeCapabilities.name,
            version: nousRuntimeCapabilities.version,
            enabled: nousRuntimeCapabilities.enabled,
            metadata: nousRuntimeCapabilities.metadata,
            updatedAt: nousRuntimeCapabilities.updatedAt,
          })
          .from(nousRuntimeCapabilities)
          .where(
            or(isNull(nousRuntimeCapabilities.userId), eq(nousRuntimeCapabilities.userId, userId)),
          )
          .orderBy(asc(nousRuntimeCapabilities.name));
        return Response.json(
          {
            ok: true,
            capabilities,
            registeredCapabilities,
            generatedAt: new Date().toISOString(),
          },
          { headers: { "Cache-Control": "private, max-age=30" } },
        );
      },
    },
  },
});
