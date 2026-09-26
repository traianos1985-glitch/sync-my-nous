import { createStart, createCsrfMiddleware, createMiddleware } from "@tanstack/react-start";

import { renderErrorPage } from "./lib/error-page";
import {
  isRateLimited,
  rejectOversizedBody,
  securityRejection,
  withSecurityHeaders,
} from "./lib/security";

const securityMiddleware = createMiddleware().server(async ({ request, next }) => {
  if (rejectOversizedBody(request)) return securityRejection(413, "Request body too large");
  if (isRateLimited(request)) return securityRejection(429, "Too many requests");
  return withSecurityHeaders(await next());
});

const errorMiddleware = createMiddleware().server(async ({ next }) => {
  try {
    return await next();
  } catch (error) {
    if (error != null && typeof error === "object" && "statusCode" in error) {
      throw error;
    }
    console.error(error);
    return new Response(renderErrorPage(), {
      status: 500,
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  }
});

// Start installs this automatically when src/start.ts is absent; defining the
// file opts out, so re-add it explicitly to keep server functions protected
// from cross-site requests.
const csrfMiddleware = createCsrfMiddleware({
  filter: (ctx) => ctx.handlerType === "serverFn",
});

export const startInstance = createStart(() => ({
  requestMiddleware: [securityMiddleware, errorMiddleware, csrfMiddleware],
}));
