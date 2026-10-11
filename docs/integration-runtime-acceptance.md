# NOUS integration and runtime acceptance checklist

This checklist separates repository CI success from end-to-end runtime validation.

## Automated gates

- Frontend: `npm ci && npm run check` (ESLint and production build).
- Python backend: install `nous-ai-os/requirements-dev.txt`, then run `python -m compileall -q executor apps *.py`, `ruff check .`, and `PYTHONPATH=. python -m pytest -q` from `nous-ai-os/`.
- Android companion: the root workflow `.github/workflows/android-companion-build.yml` builds `nous-ai-os/android_companion` and uploads a debug APK. A successful build is not an emulator/device interaction test.

## Web UI ↔ API smoke test

1. Open the deployed UI and verify the configured API status is visible.
2. Verify a valid chat request succeeds and a missing/invalid token produces a clear authentication error without retry loops.
3. Create a mission, inspect its persisted status, approve a write action, and execute it once.
4. Submit malformed JSON and an empty/malformed approval ID to `POST /api/tools/execute`; expect HTTP 400 and no approval state transition.
5. Submit an unknown, invalid, or unsupported approved tool; expect a controlled 404/409/422 response and no false successful tool-run record.
6. Send two execution requests for the same approval concurrently; at most one may claim and execute it.
7. Force a tool handler failure; verify the run and approval are marked failed and the associated mission is blocked rather than reported complete.
8. Confirm the UI displays failed, blocked, queued, running, and completed states consistently with the API response.

## Chat persistence and storage recovery

1. Load the dashboard with no local chat entry, a valid saved chat, malformed JSON, and a saved entry containing invalid message shapes. The UI should recover without crashing and keep only bounded, valid local fallback messages.
2. Verify that local fallback history is capped at 80 messages and each persisted message/citation is normalized before writing to browser storage.
3. Corrupt the conversation index in an isolated test environment. The backend must preserve the original bytes, return a controlled storage-unavailable response for chat persistence, and avoid recording secondary learning memory for an unpersisted turn.
4. Repair the index from a verified backup, then confirm conversation listing, rename, summary update, search and deletion agree on the same conversation ID.
5. Verify that corrupt auto-mission executor state and corrupt cron state are reported as unavailable and are not replaced with default state automatically.

## Shared-state authorization

- A user-scoped token must receive HTTP 401 on conversation list/read/search/rename/delete/auto-title routes because conversation storage is shared and is not yet partitioned per user.
- A user-scoped token must receive HTTP 401 on autonomous repair approval/rejection, upgrade-plan mutations, goal-manager project mutations, goal-progress refresh, release-evidence upgrade planning, and App Builder planning. Reject requests before filesystem writes, external research, or model calls.

## Scheduled autonomy and authorization

1. Use a user-scoped token against cron create/remove/toggle, workspace mission creation, NOUS Drive think, knowledge writes/uploads, document uploads and AI self-diagnosis analysis. Each sensitive mutation must return 401 without an admin token.
2. Confirm the default scheduled jobs remain available and that only morning/evening reports, backup creation and self-reflection are eligible for automatic cron approval.
3. Attempt to schedule `cleanup_disk`, `restore_data_files`, `implement_capability`, or an unknown action. Each must be rejected before a schedule file is created or changed.
4. Confirm an existing persisted cron entry with a disallowed action is not executed or auto-approved.
5. Check diagnostic API responses for unavailable components; they may report error types, but must not disclose exception text, tokens, or private filesystem paths.

## Android companion device test

1. Build and install the debug APK on a test device.
2. Enable the accessibility service manually and verify the app reports whether the service is connected.
3. Through the existing ADB bridge, issue `state`, `ui_tree`, `back`, `home`, and a harmless in-bounds `tap`; verify truthful results.
4. Confirm unknown commands and invalid/non-finite coordinates are rejected.
5. Verify UI-tree text is not written to logcat. UI trees can contain private on-screen text, so treat returned snapshots as sensitive.
6. On Android 14+, verify broadcasts from an ordinary third-party app are rejected by sender UID. On older Android versions, the platform does not expose the same sender UID check through this API; do not treat the exported ADB receiver as protected against arbitrary local apps on those versions.
7. Test the actual supported Android versions; a successful APK build does not prove runtime behavior across OEMs or accessibility settings.

## Cost-bearing and resource-intensive endpoints

1. Call both `/api/gemini-check` and `/gemini-check` with a user-scoped token. They must return 401 before invoking Gemini; an admin token with a prompt over 500 characters must return 400 without a provider call.
2. Call `/remote/executive/plan` and `/remote/quality-gate/run` with a user-scoped token. They must return 401 before starting planning or quality checks.
3. Verify quality-gate file lists are JSON arrays with no more than 50 entries and each path string is bounded; malformed input must return 400 without starting checks.
4. Verify the normal dashboard Gemini connection test still works with the configured admin/master token and the short built-in test prompt.

## Deployment and recovery checks

- Verify the GitHub Pages build and the live backend separately after merge.
- Check API base URL, authentication configuration, CORS, database availability, and Render cold-start behavior without printing credentials to logs.
- Reboot the backend during a queued/running mission in a test environment; verify recovery and final mission status before enabling autonomous production use.
- Keep deployment secrets in server-side secret settings, never in client bundles or committed files.
