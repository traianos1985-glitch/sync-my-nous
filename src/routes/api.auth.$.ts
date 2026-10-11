import { createFileRoute } from "@tanstack/react-router";

async function handleAuth(request: Request) {
  const { auth } = await import("../lib/auth");
  return auth.handler(request);
}

export const Route = createFileRoute("/api/auth/$")({
  server: {
    handlers: {
      GET: ({ request }) => handleAuth(request),
      POST: ({ request }) => handleAuth(request),
    },
  },
});
