async function getAuthSession(request: Request) {
  const { auth } = await import("./auth");
  return auth.api.getSession({ headers: request.headers });
}

export async function getAuthenticatedUserId(request: Request) {
  try {
    const session = await getAuthSession(request);
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
