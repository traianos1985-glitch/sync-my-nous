import { createFileRoute } from "@tanstack/react-router";
import { sql } from "drizzle-orm";
import { db } from "../lib/db";

// The Gemini key lives on the Render backend (service `nous-ai-os`), never here.
// The web app only ever needs the NOUS token, so health is judged by whether the
// NOUS API that powers chat/status/Gemini is actually reachable.
const NOUS_API_FALLBACK = "https://nous-ai-os-api.onrender.com";
const nousApiBase = (process.env["NOUS_API_URL"] ?? NOUS_API_FALLBACK).replace(/\/+$/, "");

async function checkNousApi(): Promise<"ok" | "degraded" | "unreachable"> {
  try {
    const response = await fetch(`${nousApiBase}/health`, {
      signal: AbortSignal.timeout(5_000),
    });
    if (!response.ok) return "degraded";
    const body = (await response.json()) as { system?: string };
    return body.system === "healthy" ? "ok" : "degraded";
  } catch {
    return "unreachable";
  }
}

export const Route = createFileRoute("/api/health")({
  server: {
    handlers: {
      GET: async () => {
        const startedAt = performance.now();
        const [nousApi, database] = await Promise.all([
          checkNousApi(),
          db
            .execute(sql`SELECT 1`)
            .then(() => "ok" as const)
            .catch(() => "unavailable" as const),
        ]);

        // Local Postgres only backs the optional server-side routes (better-auth
        // sessions, local chat history); the dashboard runs entirely on the NOUS
        // API, so it is reported but never makes the app unhealthy on its own.
        const checks = {
          database,
          nousApi,
          aiGateway: nousApi === "ok" ? "render" : "unavailable",
          localGeminiKey: process.env["GEMINI_API_KEY"] || process.env["GCP_API_KEY"]
            ? "configured"
            : "not-needed",
          research: "available",
        } as const;

        const healthy = nousApi === "ok";
        return Response.json(
          {
            ok: healthy,
            status: healthy ? "healthy" : "degraded",
            checks,
            latencyMs: Math.round(performance.now() - startedAt),
            timestamp: new Date().toISOString(),
            uptimeSeconds: Math.round(process.uptime()),
          },
          {
            status: healthy ? 200 : 503,
            headers: { "Cache-Control": "no-store" },
          },
        );
      },
    },
  },
});
