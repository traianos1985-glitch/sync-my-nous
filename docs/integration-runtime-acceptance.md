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

## Android companion device test

1. Build and install the debug APK on a test device.
2. Enable the accessibility service manually and verify the app reports whether the service is connected.
3. Through the existing ADB bridge, issue `state`, `ui_tree`, `back`, `home`, and a harmless in-bounds `tap`; verify truthful results.
4. Confirm unknown commands and invalid/non-finite coordinates are rejected.
5. Verify UI-tree text is not written to logcat. UI trees can contain private on-screen text, so treat returned snapshots as sensitive.
6. On Android 14+, verify broadcasts from an ordinary third-party app are rejected by sender UID. On older Android versions, the platform does not expose the same sender UID check through this API; do not treat the exported ADB receiver as protected against arbitrary local apps on those versions.
7. Test the actual supported Android versions; a successful APK build does not prove runtime behavior across OEMs or accessibility settings.

## Deployment and recovery checks

- Verify the GitHub Pages build and the live backend separately after merge.
- Check API base URL, authentication configuration, CORS, database availability, and Render cold-start behavior without printing credentials to logs.
- Reboot the backend during a queued/running mission in a test environment; verify recovery and final mission status before enabling autonomous production use.
- Keep deployment secrets in server-side secret settings, never in client bundles or committed files.
