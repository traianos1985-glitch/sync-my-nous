import { createFileRoute } from "@tanstack/react-router";
import { openApiDocument } from "../lib/openapi";

export const Route = createFileRoute("/api/openapi")({
  server: {
    handlers: {
      GET: () =>
        Response.json(openApiDocument, { headers: { "Cache-Control": "public, max-age=300" } }),
    },
  },
});
