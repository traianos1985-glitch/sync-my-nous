# Full-stack readiness and regression gates

This checklist complements the staged hosting migration runbook and helps prevent the static frontend, TanStack Start server routes and existing Flask API from silently drifting apart.

## Routing contract

| Request family | Expected destination | Authentication boundary |
| --- | --- | --- |
| `/api/chat`, `/api/health` | Existing Flask service on Render | NOUS bearer token where required by the Flask endpoint |
| `/api/approvals`, `/api/audit`, `/api/evaluation`, `/api/feedback`, `/api/jobs` | Same-origin TanStack server routes | Better Auth session; endpoint-specific authorization |
| `/api/knowledge*`, `/api/missions*`, `/api/observability` | Same-origin TanStack server routes | Better Auth session; user-scoped data access |
| `/api/security-audit`, `/api/security-lessons`, `/api/status`, `/api/tools/execute` | Same-origin TanStack server routes | Better Auth session and action-specific safety checks |
| `/api/chat/stream` | Same-origin TanStack streaming route | Same session and authorization policy as the corresponding UI action |

The API client contract check verifies that every declared same-origin prefix has a matching route file and that the allowlist remains aligned with the expected contract. It is a static regression guard, not a substitute for runtime authorization or end-to-end tests.

## Required checks for every pull request

Run from the repository root:

```sh
npm ci
npm run check
npm run format:check
npm run test:python
```

The frontend check includes lint, TypeScript, production build, public-bundle secret scanning and API route contract validation. CI independently runs Python syntax checks, Ruff, pytest, dependency audit and repository/history secret scanning.

## Preview deployment acceptance gates

Do not change the production domain or remove the current GitHub Pages / Render deployment until all applicable checks pass on a preview deployment.

1. **Build and routing**
   - Confirm the provider deploys TanStack Start server handlers, not just static assets.
   - Confirm landing, sign-in and dashboard pages load on refresh and direct URL.
   - Confirm each same-origin API family reaches its expected handler; JSON endpoints must not return an HTML fallback or be accidentally routed to Flask.
   - Confirm streaming chat emits incremental data and handles disconnects cleanly.
2. **Authentication and authorization**
   - Unauthenticated requests to protected server endpoints return 401.
   - An authenticated user can access only their own missions, tool runs, knowledge and observability records.
   - A session cookie is not accepted as a NOUS bearer token, and a NOUS token is not treated as a Better Auth session.
   - Invalid, expired and revoked credentials fail closed.
3. **Secrets and configuration**
   - Confirm `DATABASE_URL`, a strong `BETTER_AUTH_SECRET` (or approved `SESSION_SECRET`) and the correct auth base URL are configured server-side.
   - Keep `GEMINI_API_KEY` server-side in the existing provider/backend.
   - Never place secrets in `VITE_*` variables, client bundles, source maps, logs or test fixtures.
   - Verify environment variable names and deployment logs in the hosting provider dashboard; repository source cannot prove provider secrets exist or are correct.
4. **Persistence and failure handling**
   - Apply schema migrations to a preview database and test backup/restore before production data changes.
   - Missing database connectivity must yield a controlled error, not a false healthy status or secret-bearing stack trace.
   - Rate limits, provider quota failures and cold starts must produce actionable, non-sensitive errors.
5. **UI-to-API coverage**
   - Every navigation entry opens a real panel or explicitly documented custom renderer.
   - Every visible action has success, loading, empty and failure states.
   - Exercise chat, missions, jobs, approvals, knowledge, feedback, audit, observability, security controls and tool execution from the actual UI.
   - Test mobile and desktop viewports.

Record the preview URL, commit SHA, test results, failures and reviewer approval in the PR before production cutover.

## Rollback

- Keep the previous frontend deployment and the Render Flask API available.
- Roll back by restoring the previous frontend deployment / domain target; do not delete production data or rotate unrelated credentials as part of rollback.
- For schema changes, use a documented backward-compatible migration and verified backup. Application rollback does not automatically reverse a database migration.
- After rollback, re-test sign-in, NOUS-token chat, core UI navigation and server health.

## Limits of automated checks

Passing CI does not prove provider configuration, external service availability, production authentication, cross-user isolation or every UI action. Those require a preview deployment and real smoke tests.
