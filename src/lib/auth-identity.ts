import { auth } from "./auth";

export async function getAuthenticatedUserId(request: Request) {
  try {
    const session = await auth.api.getSession({ headers: request.headers });
    return session?.user?.id ?? null;
  } catch (error) {
    console.warn("[nous] session lookup failed", error instanceof Error ? error.message : error);
    return null;
  }
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
