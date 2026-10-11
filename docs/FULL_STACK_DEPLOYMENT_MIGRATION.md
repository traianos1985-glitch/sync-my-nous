# Full-stack deployment migration (staged)

## Goal

Run the React/TanStack Start workspace with its server routes on a full-stack host while retaining the existing Flask NOUS API on Render. The migration must not require a one-step cutover and must not silently change the current token-based NOUS workflow.

The repository currently advertises `https://sync-my-nous.vercel.app` as its homepage, but repository metadata alone does not prove that the deployed app is serving TanStack server routes. Treat it as a candidate preview/target until the smoke checks below pass.

## Current components to preserve

- **UI:** React/TanStack Start dashboard and landing page.
- **Existing NOUS API:** `https://nous-ai-os-api.onrender.com` (Flask service).
- **Model provider:** Gemini key stays server-side in Render; never copy it into Vite/client variables.
- **NOUS token:** current dashboard stores the token in session storage and sends it as a Bearer token to the Flask API.
- **TanStack server API:** same-origin routes under `/api/*`, including approvals, audit, evaluation, feedback, jobs, knowledge, missions, observability, security audit/lessons, status, tool execution and streaming chat.
- **Database/session auth:** Better Auth uses a Postgres dialect and expects production auth secrets/base URL plus a reachable database.

## Non-negotiable safety rules

1. Do not remove, repoint, or disable GitHub Pages or the Render Flask service during preview work.
2. Do not change the production URL until the full smoke suite passes against the new host.
3. Do not copy production secrets into Git, client-side `VITE_*` variables, build logs, or screenshots.
4. Do not treat a supplied user ID as authentication. Session-protected endpoints must validate a real Better Auth session, or a separately reviewed server-side token-to-identity bridge.
5. Do not point the new host at production data until database schema/migrations, backup, and rollback are verified.
6. A successful static build is not proof that server routes are deployed.

## Phase 0 — inspect the current deployment

Before changing hosting settings, verify in the hosting provider dashboard:
- Which GitHub repository and branch are connected.
- Build command, output/framework preset, and deployment logs.
- Whether the production deployment emits a server function for TanStack Start, not only static assets.
- Runtime environment variable *names and presence* (never print secret values): `DATABASE_URL`, `BETTER_AUTH_SECRET` or `SESSION_SECRET`, `BETTER_AUTH_URL`, and the relevant Vercel URL variables.
- Whether a database is provisioned and the current schema is migrated.
- Whether the existing domain is a production or preview deployment.

The repository connector cannot inspect provider secrets or environment settings; these checks must be confirmed in the provider dashboard.

## Phase 1 — preview-only server-route smoke test

Use a preview URL, not the current primary URL. Verify all of the following:
- The landing page and `/dashboard` load directly, including a hard refresh.
- A known server route is reached on the same origin and returns an application response rather than a static HTML fallback (for example, `/api/health` or `/api/status`, according to the route's documented auth requirements).
- A deliberately unauthenticated request to a protected endpoint is rejected with the expected 401/403, not a 404 or HTML.
- Better Auth session endpoints respond and the sign-in/session flow can establish a cookie with correct Secure/SameSite/domain settings.
- Streaming chat uses the server route and preserves cancellation/error behavior.
- The NOUS token continues to call the existing Render API; the Gemini key remains on Render.
- No private environment value appears in client JS, source maps, build output or logs.

Do not use live write operations during the first pass. Use read-only requests and a test account/database.

## Phase 2 — reconcile the two authentication paths

The dashboard currently presents a NOUS Bearer-token workflow, while TanStack routes call `auth.api.getSession()` through `requireAuthenticatedUserId()`. These are distinct authentication mechanisms. Before relying on user-scoped TanStack APIs, choose and test one explicit design:

- **Preferred:** provide a real Better Auth sign-in/session flow for the dashboard and keep the NOUS token scoped to the separate Flask API; or
- implement a server-side, narrowly scoped token-to-identity bridge only if the NOUS backend can validate the token and map it to a trusted identity.

Never trust a client-provided user ID or assume that a valid Flask token automatically creates a Better Auth session.

## Phase 3 — end-to-end feature checks

Test in preview with a test user and non-production data:
- status and health;
- chat and SSE streaming;
- missions and mission streaming;
- approvals/rejections and audit trail;
- jobs create/read/cancel/retry;
- knowledge upload/search/process;
- evaluation and feedback;
- observability and defensive security endpoints;
- tool execution policy, including approval before side effects;
- mobile viewport, refresh/deep links, token entry, logout/session expiry;
- database persistence across a new session and a redeploy.

For every check, record URL, expected status, actual status, and evidence. A rendered button is not proof its backend action works.

## Phase 4 — controlled cutover and rollback

Only after Phases 0–3 pass:
1. Record the current production URLs and deployment revisions.
2. Confirm a restorable database backup and documented migration rollback.
3. Promote the verified full-stack deployment and update the primary link only if required.
4. Keep the previous GitHub Pages and Render deployments available during the observation window.
5. Roll back the primary URL immediately if authentication, chat, persistence, or safety/approval checks regress.

## Exit criteria

Migration is complete only when the server routes are demonstrably served by the full-stack host, the correct authentication path is proven, the main UI/API contract suite passes, and rollback has been tested. This runbook is a plan, not a claim that the production migration has already occurred.
