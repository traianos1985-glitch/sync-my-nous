# Full-stack deployment migration (staged)

## Goal

Run the React/TanStack Start workspace with its server routes on a full-stack
host while retaining the existing Flask NOUS API on Render. Avoid a one-step
cutover and do not silently change the current token-based NOUS workflow.

The repository advertises `https://sync-my-nous.vercel.app` as its homepage.
That alone does not prove the deployed app serves TanStack server routes. Treat
it as a candidate target until the smoke checks below pass.

## Current components to preserve

- **UI:** React/TanStack Start dashboard and landing page.
- **Existing NOUS API:** `https://nous-ai-os-api.onrender.com` (Flask service).
- **Model provider:** Gemini key stays server-side in Render. Never copy it
  into Vite/client variables.
- **NOUS token:** the dashboard stores the token in session storage and sends
  it as a Bearer token to the Flask API.
- **TanStack server API:** same-origin `/api/*` routes for approvals, audit,
  evaluation, feedback, jobs, knowledge, missions, observability, security
  audit/lessons, status, tool execution and streaming chat.
- **Database/session auth:** Better Auth uses Postgres and expects production
  auth secrets, a base URL and a reachable database.

## Non-negotiable safety rules

1. Do not remove, repoint or disable GitHub Pages or the Render Flask service
   during preview work.
2. Do not change the production URL until the full smoke suite passes.
3. Never commit secrets or expose them through client-side `VITE_*` variables,
   build logs or screenshots.
4. Never treat a supplied user ID as authentication. Session-protected
   endpoints must validate a real Better Auth session or use a separately
   reviewed server-side token-to-identity bridge.
5. Do not connect the new host to production data until schema migrations,
   backup and rollback are verified.
6. A successful static build does not prove that server routes are deployed.

## Phase 0 — inspect the current deployment

Before changing hosting settings, verify in the provider dashboard:

- Which GitHub repository and branch are connected.
- Build command, output/framework preset and deployment logs.
- Whether the deployment emits a server function for TanStack Start, not only
  static assets.
- Presence of these environment variable names (never print secret values):
  `DATABASE_URL`, `BETTER_AUTH_SECRET` or `SESSION_SECRET`,
  `BETTER_AUTH_URL`, and the relevant Vercel URL variables.
- Whether a database is provisioned and the schema is migrated.
- Whether the existing domain is a production or preview deployment.

The repository connector cannot inspect provider secrets or environment
settings. Confirm these items in the hosting provider dashboard.

## Phase 1 — preview-only server-route smoke test

Use a preview URL, not the current primary URL. Verify all of the following:

- The landing page and `/dashboard` load directly, including a hard refresh.
- A known server route returns an application response, not static fallback
  HTML (for example, `/api/health` or `/api/status`, according to its auth
  requirements).
- An unauthenticated request to a protected endpoint returns the expected
  401/403, not a 404 or HTML page.
- Better Auth session endpoints respond and sign-in can establish a cookie
  with correct Secure, SameSite and domain settings.
- Streaming chat uses the server route and preserves cancellation/error behavior.
- The NOUS token still calls the existing Render API; the Gemini key stays on
  Render.
- No private environment value appears in client JS, source maps, build output
  or logs.

Do not use live write operations during the first pass. Use a test account and
non-production database.

## Phase 2 — reconcile the two authentication paths

The dashboard presents a NOUS Bearer-token workflow, while TanStack routes call
`auth.api.getSession()` through `requireAuthenticatedUserId()`. These are
distinct authentication mechanisms. Choose and test one explicit design before
relying on user-scoped TanStack APIs.

- **Preferred:** provide a real Better Auth sign-in/session flow for the
  dashboard and keep the NOUS token scoped to the separate Flask API.
- Alternatively, implement a server-side, narrowly scoped token-to-identity
  bridge only if the NOUS backend can validate the token and map it to a
  trusted identity.

Never trust a client-provided user ID or assume that a valid Flask token
automatically creates a Better Auth session.

## Phase 3 — end-to-end feature checks

Test in preview with a test user and non-production data:

- Status and health.
- Chat and SSE streaming.
- Missions and mission streaming.
- Approvals/rejections and audit trail.
- Jobs: create, read, cancel and retry.
- Knowledge: upload, search and process.
- Evaluation and feedback.
- Observability and defensive security endpoints.
- Tool execution policy, including approval before side effects.
- Mobile viewport, refresh/deep links, token entry, logout and session expiry.
- Database persistence across a new session and a redeploy.

For every check, record the URL, expected status, actual status and evidence.
A rendered button is not proof that its backend action works.

## Phase 4 — controlled cutover and rollback

Only after Phases 0–3 pass:

1. Record the current production URLs and deployment revisions.
2. Confirm a restorable database backup and documented migration rollback.
3. Promote the verified full-stack deployment and update the primary link only
   if required.
4. Keep the previous GitHub Pages and Render deployments available during the
   observation window.
5. Roll back the primary URL if authentication, chat, persistence or safety
   and approval checks regress.

## Exit criteria

Migration is complete only when server routes are demonstrably served by the
full-stack host, the correct authentication path is proven, the main UI/API
contract suite passes and rollback has been tested. This runbook is a plan,
not a claim that the production migration has already occurred.
