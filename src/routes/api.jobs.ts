import { createFileRoute } from "@tanstack/react-router";
import { createJob, getJob } from "../lib/db/jobs";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { isAllowedJobKind, NOUS_LIMITS, serializedBytes } from "../lib/platform-policy";

async function userId(request: Request) {
  return requireAuthenticatedUserId(request);
}

export const Route = createFileRoute("/api/jobs")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const body = (await request.json()) as { kind?: string; payload?: unknown };
        if (
          !body.kind ||
          body.kind.length > NOUS_LIMITS.maxJobKindLength ||
          !isAllowedJobKind(body.kind)
        )
          return Response.json({ error: "Unsupported job kind" }, { status: 400 });
        if (serializedBytes(body.payload) > NOUS_LIMITS.maxToolPayloadBytes)
          return Response.json({ error: "Job payload is too large" }, { status: 413 });
        const job = await createJob(await userId(request), body.kind, body.payload ?? {});
        return Response.json({ job }, { status: 202 });
      },
      GET: async ({ request }) => {
        const id = new URL(request.url).searchParams.get("id");
        if (!id) return Response.json({ error: "Missing job id" }, { status: 400 });
        const job = await getJob(id, await userId(request));
        return job
          ? Response.json({ job })
          : Response.json({ error: "Job not found" }, { status: 404 });
      },
    },
  },
});
