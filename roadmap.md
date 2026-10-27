# Roadmap

- [ ] Split dashboard into independent views, connection settings, navigation and state hook.
- [ ] Harden Render wake-up tracking, cancellation, retries and non-overlapping polling; verify tests and UI.

- [x] Fix broken build (vite config)
- [x] Home ↔ dashboard link
- [x] Loop: crash-safe cycles + backoff
- [x] API: resilient /overview, new /api/system/metrics, uptime
- [x] Cloud: Procfile uses PORT/gunicorn, render.yaml, docker port fix
- [x] Dashboard live data from NOUS API (Render URL, token auth, timeout handling, CORS)
- [x] nous-api.ts: always call Render directly (no /api/nous relative base); backend accepts https://*.lovable.app / .lovableproject.com / .lovable.dev origins

- [x] Lint & Build Cleanups: split route components from exports, clean Vite/path settings, verify checks and merge into main.
