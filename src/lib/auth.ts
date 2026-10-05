import { betterAuth } from "better-auth";
import { randomUUID } from "node:crypto";
import { pool } from "./db";

const resolvedSecret =
  process.env["BETTER_AUTH_SECRET"] ??
  process.env["SESSION_SECRET"] ??
  (process.env["NODE_ENV"] === "production" ? undefined : `dev-only-secret-${randomUUID()}`);

if (!resolvedSecret && process.env["NODE_ENV"] === "production") {
  console.error(
    "[nous] FATAL: BETTER_AUTH_SECRET (or SESSION_SECRET) must be set in production. Auth will not function securely.",
  );
}

export const auth = betterAuth({
  secret: resolvedSecret,
  database: {
    db: pool,
    type: "postgres",
    schemaName: "neon_auth",
  },
  baseURL:
    process.env["BETTER_AUTH_URL"] ??
    (process.env["VERCEL_PROJECT_PRODUCTION_URL"]
      ? `https://${process.env["VERCEL_PROJECT_PRODUCTION_URL"]}`
      : process.env["VERCEL_URL"]
        ? `https://${process.env["VERCEL_URL"]}`
        : process.env["V0_RUNTIME_URL"]),
  emailAndPassword: { enabled: true, autoSignIn: true },
  trustedOrigins: [
    ...(process.env["REPLIT_DEV_DOMAIN"] ? [`https://${process.env["REPLIT_DEV_DOMAIN"]}`] : []),
    ...(process.env["NODE_ENV"] === "development"
      ? [
          "http://localhost:3000",
          ...["V0_RUNTIME_URL", "V0_DEV_APP_URL", "V0_BUILD_URL", "V0_SANDBOX_URL"]
            .map((key) => process.env[key])
            .filter((value): value is string => Boolean(value)),
        ]
      : []),
    ...(process.env["NODE_ENV"] === "production"
      ? [
          ...(process.env["VERCEL_URL"] ? [`https://${process.env["VERCEL_URL"]}`] : []),
          ...(process.env["VERCEL_PROJECT_PRODUCTION_URL"]
            ? [`https://${process.env["VERCEL_PROJECT_PRODUCTION_URL"]}`]
            : []),
        ]
      : []),
  ],
  session: { expiresIn: 60 * 60 * 24 * 7, updateAge: 60 * 60 * 24 },
  ...(process.env["NODE_ENV"] === "development"
    ? { advanced: { defaultCookieAttributes: { sameSite: "none" as const, secure: true } } }
    : {}),
});
