const requestLog = new Map<string, { count: number; resetAt: number }>();
const WINDOW_MS = 60_000;
const MAX_REQUESTS = 120;
const MAX_BODY_BYTES = 1_048_576;

export function rateLimitKey(request: Request, scope = "global") {
  return `${scope}:${getClientKey(request)}`;
}

export function getClientKey(request: Request) {
  return request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
}

export async function isDatabaseRateLimited(
  request: Request,
  db: { execute: (query: unknown) => Promise<unknown> },
  sql: (strings: TemplateStringsArray, ...values: unknown[]) => unknown,
  scope = "global",
) {
  const key = rateLimitKey(request, scope);
  const result = (await db.execute(
    sql`SELECT request_count, window_started_at FROM nous_rate_limits WHERE user_id = ${key}`,
  )) as { rows?: Array<{ request_count: number; window_started_at: string }> };
  const row = result.rows?.[0];
  const now = Date.now();
  const windowStarted = row ? new Date(row.window_started_at).getTime() : now;
  const count = row && now - windowStarted < WINDOW_MS ? row.request_count + 1 : 1;
  await db.execute(
    sql`INSERT INTO nous_rate_limits (user_id, window_started_at, request_count) VALUES (${key}, NOW(), ${count}) ON CONFLICT (user_id) DO UPDATE SET window_started_at = CASE WHEN ${now} - EXTRACT(EPOCH FROM nous_rate_limits.window_started_at) * 1000 >= ${WINDOW_MS} THEN NOW() ELSE nous_rate_limits.window_started_at END, request_count = CASE WHEN ${now} - EXTRACT(EPOCH FROM nous_rate_limits.window_started_at) * 1000 >= ${WINDOW_MS} THEN 1 ELSE nous_rate_limits.request_count + 1 END`,
  );
  return count > MAX_REQUESTS;
}

export function isRateLimited(request: Request) {
  const now = Date.now();
  const key = getClientKey(request);
  if (requestLog.size > 10_000) {
    for (const [loggedKey, value] of requestLog) {
      if (value.resetAt <= now) requestLog.delete(loggedKey);
    }
  }
  const current = requestLog.get(key);
  if (!current || current.resetAt <= now) {
    requestLog.set(key, { count: 1, resetAt: now + WINDOW_MS });
    return false;
  }
  current.count += 1;
  return current.count > MAX_REQUESTS;
}

export function securityHeaders() {
  return {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Content-Security-Policy-Report-Only":
      "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self' https:; font-src 'self' data: https:; form-action 'self'",
  };
}

export function rejectOversizedBody(request: Request) {
  const length = Number(request.headers.get("content-length") ?? 0);
  return Number.isFinite(length) && length > MAX_BODY_BYTES;
}

export function withSecurityHeaders(response: Response) {
  const headers = new Headers(response.headers);
  for (const [name, value] of Object.entries(securityHeaders())) headers.set(name, value);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export function securityRejection(status: 413 | 429, error: string) {
  return withSecurityHeaders(
    Response.json({ error }, { status, headers: { "Retry-After": "60" } }),
  );
}
