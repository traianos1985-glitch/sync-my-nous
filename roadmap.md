# Roadmap

- [x] Add App Builder Studio file explorer, code viewer, streaming validation console and approved run/logs/stop/download controls.
- [x] Add Self-Healing diagnosis and diff review with explicit approve/reject, stale-baseline checks and no launch-time rewriting; verify frontend and Python regression suites.
- [ ] Verify hosted Studio lifecycle; requires owner-entered NOUS token and any needed Render redeploy.

- [x] Connect chat to bounded, read-only ReAct tool execution with structured execution records and streamed status.
- [x] Display expandable AI Elements tool calls and retain them in chat sessions; verified execution, normalization, transport and existing regression tests.
- [ ] Verify hosted tool execution; requires Render redeploy and owner-entered NOUS token.

- [x] Add browser-local multi-session chat history with rename, search and session URLs.
- [x] Add document drop zone, ingestion status and knowledge search filters.
- [x] Unify Python missions and task claims in SQLite with legacy migration and persistence tests.

- [x] Split dashboard into independent views, connection settings, navigation and state hook.
- [x] Harden Render wake-up tracking, cancellation, retries and non-overlapping polling; verified 18 request tests, 8 dashboard contract tests, 3 config tests and preview navigation/wake indicator.
- [ ] Verify live authenticated chat and mission actions; owner must enter the real NOUS token through the dashboard Settings field.

- [x] Fix broken build (vite config)
- [x] Home ↔ dashboard link
- [x] Loop: crash-safe cycles + backoff
- [x] API: resilient /overview, new /api/system/metrics, uptime
- [x] Cloud: Procfile uses PORT/gunicorn, render.yaml, docker port fix
- [x] Dashboard live data from NOUS API (Render URL, token auth, timeout handling, CORS)
- [x] nous-api.ts: always call Render directly (no /api/nous relative base); backend accepts https://*.lovable.app / .lovableproject.com / .lovable.dev origins

- [x] Lint & Build Cleanups: split route components from exports, clean Vite/path settings, verify checks and merge into main.
- [x] CI Lockfile Sync & Render Wake Timer: sync package-lock.json with package.json dependencies and add live cold-start counter to wake banner.
- [x] Chat Workspace & Code Blocks: syntax-styled code blocks with copy button, individual message copy, Markdown & JSON chat export with metadata, and dedicated test suite.
- [x] Telemetry & Observability Cards: add bounded CPU/memory history, uptime and mission count snapshots, mission status distribution, and Gemini connection state to the dashboard.
- [x] Approvals Inspector & Mission Operations: expandable payload inspector with JSON formatting and copy action for pending approvals, manual approval queue refresh, and interactive mission tab filtering with instant search.
- [x] Global Keyboard Shortcuts & Command Palette Suite: enhanced Command Menu with quick actions (Gemini test, approvals queue refresh, API base copy, shortcut cheat sheet), header approvals indicator pill, global Alt+1..5 navigation with '?' shortcuts modal, and dedicated approvals view wiring.

- [ ] Apply Python updates to Render and verify authenticated document upload/search; requires owner redeploy and NOUS token in Settings.
