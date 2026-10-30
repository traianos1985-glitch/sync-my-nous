import { createFileRoute } from "@tanstack/react-router";
import { requireAuthenticatedUserId } from "../lib/auth-identity";
import { getExecutionReceipt, verifyExecutionReceipt } from "../lib/receipt-service";

function isWorkerAuthorized(request: Request) {
  const token = process.env["NOUS_WORKER_TOKEN"];
  return Boolean(token && request.headers.get("authorization") === `Bearer ${token}`);
}

export const Route = createFileRoute("/api/receipts")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const userId = await requireAuthenticatedUserId(request);
        const id = new URL(request.url).searchParams.get("id");
        if (!id) return Response.json({ error: "id is required" }, { status: 400 });
        const receipt = await getExecutionReceipt(userId, id);
        return receipt
          ? Response.json({ receipt })
          : Response.json({ error: "Receipt not found" }, { status: 404 });
      },
      POST: async ({ request }) => {
        if (!isWorkerAuthorized(request))
          return Response.json({ error: "Unauthorized" }, { status: 401 });
        const body = (await request.json()) as {
          userId?: unknown;
          id?: unknown;
          verification?: unknown;
        };
        if (
          typeof body.userId !== "string" ||
          typeof body.id !== "string" ||
          !body.verification ||
          typeof body.verification !== "object"
        )
          return Response.json(
            { error: "userId, id and verification are required" },
            { status: 400 },
          );
        const receipt = await verifyExecutionReceipt(
          body.userId,
          body.id,
          body.verification as Record<string, unknown>,
        );
        return receipt
          ? Response.json({ ok: true, receipt })
          : Response.json({ error: "Receipt not found" }, { status: 404 });
      },
    },
  },
});
