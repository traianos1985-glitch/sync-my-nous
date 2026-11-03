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
- [x] Autonomy Control & Live Feed: console to start/pause NOUS autonomous cycles, configure intervals (5-86400s) with presets, monitor heartbeat/watchdog silence and battery guard, live audit timeline/activity feed with filtering and JSON payload inspection, and safety controls with persistent Emergency Stop kill switch.
- [x] Autonomy Control & Live Feed: console to start/pause NOUS autonomous cycles, configure intervals (5-86400s) with presets, monitor heartbeat/watchdog silence and battery guard, live audit timeline/activity feed with filtering and JSON payload inspection, and safety controls with persistent Emergency Stop kill switch.
- [x] Autonomous Browser & Web Operator Studio: interactive web navigation & content extraction reader, quick targets, deep AI research & search engine, Playwright browser driver actions builder with execution console, remote browser bridge worker queue manager, and continuous web intelligence topics viewer with research cycle triggers.
- [x] Interactive App Sandbox & Testing Suite: interactive sandbox environment to run, test, and inspect NOUS-generated apps with live responsive/tablet/mobile web preview iframe, automated test suite runner, mock API endpoint tester with presets, real-time filtered process logs, launch/approval/restart/stop controls, and zip download.
- [x] Global Keyboard Shortcuts & Command Palette Suite: enhanced Command Menu with quick actions (Gemini test, approvals queue refresh, API base copy, shortcut cheat sheet), header approvals indicator pill, global Alt+1..5 navigation with '?' shortcuts modal, and dedicated approvals view wiring.- [x] Global Keyboard Shortcuts & Command Palette Suite: enhanced Command Menu with quick actions (Gemini test, approvals queue refresh, API base copy, shortcut cheat sheet), header approvals indicator pill, global Alt+1..5 navigation with '?' shortcuts modal, and dedicated approvals view wiring.

- [ ] Apply Python updates to Render and verify authenticated document upload/search; requires owner redeploy and NOUS token in Settings.

- [x] Audit N-03: managed autonomy background loop (start/stop/reconcile, truthful loop_running)
- [x] Audit N-05: real mission actions (search_web, read_url, search_memory, knowledge_search, code_analysis, app_validation, agent_task)
- [x] Audit N-06: browser host-support status + url_reader/web_search fallback so research jobs complete
- [x] Audit N-07: knowledge memory locked atomic writes, size limits, provenance
- [x] Audit F-04: short Git SHA prefix matching in fleet versions_match
- [x] Audit N-01: app launch env allowlist (verify + test)
- [x] Tests for all of the above, full suite green
- [ ] Verify audit upgrades live on Render; requires owner redeploy of `nous-ai-os` and NOUS token in Settings.

- [x] GitHub & Pages safety: missing/invalid token banner, write actions disabled without token, dry-run publish preview, secret file exclusion, token redaction, honest partial results; mocked tests only.
- [ ] Verify GitHub Operator live; requires Render redeploy, NOUS token in Settings and a GitHub token.
- [ ] Interactive Field Assistant & Larmor Studio: contextual chat, unit-safe calculator, explicit field diary saves, scientific safeguards, tests and GitHub delivery.

- [ ] Image upgrades (Nov 3): Swarm tab in UI, Android Companion setup/status screen with honest host detection, per-message read-aloud in chat (mic/TTS already exist), storage durability status + warning, 24/7 external scheduler endpoint `/remote/service/cycle` + setup guide; tests.
- [ ] Durable external database (PostgreSQL) for Render Free; needs owner decision on provider (Render disk vs external Postgres).
