import { auth } from "./auth";

export async function getAuthenticatedUserId(request: Request) {
  const session = await auth.api.getSession({ headers: request.headers });
  return session?.user?.id ?? null;
}

export async function requireAuthenticatedUserId(request: Request) {
  const userId = await getAuthenticatedUserId(request);
  if (!userId)
    throw new Response(JSON.stringify({ error: "Authentication required" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  return userId;
}
