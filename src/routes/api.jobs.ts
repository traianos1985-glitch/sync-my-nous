import { createFileRoute } from "@tanstack/react-router";
import { createJob, getJob } from "../lib/db/jobs";

function userId(request: Request) {
  return request.headers.get("x-nous-user-id")?.trim().slice(0, 128) || "anonymous";
}

export const Route = createFileRoute("/api/jobs")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const body = (await request.json()) as { kind?: string; payload?: unknown };
        if (!body.kind || body.kind.length > 80)
          return Response.json({ error: "Invalid job kind" }, { status: 400 });
        const job = await createJob(userId(request), body.kind, body.payload ?? {});
        return Response.json({ job }, { status: 202 });
      },
      GET: async ({ request }) => {
        const id = new URL(request.url).searchParams.get("id");
        if (!id) return Response.json({ error: "Missing job id" }, { status: 400 });
        const job = await getJob(id, userId(request));
        return job
          ? Response.json({ job })
          : Response.json({ error: "Job not found" }, { status: 404 });
      },
    },
  },
});
