## Runtime setup for agents (read before testing or changing credentials)

- The deployed backend is `https://nous-ai-os-api.onrender.com`.
- The Gemini API key (`GEMINI_API_KEY`) is already configured as a server-side environment variable on the Render service `nous-ai-os`. **Do not ask the owner for it, expose it in the frontend, add it to a `VITE_*` variable, or commit it.**
- When opening the app in a preview, the owner will enter the **NOUS token** in the app's token field. Use that token only to authenticate requests to the deployed NOUS backend; do not ask for the Gemini key instead.
- Never hard-code, log, screenshot, or commit the NOUS token. Do not put it in source files, test fixtures, URLs, browser-visible build variables, or pull-request descriptions. Use the app's intended token input / Authorization header.
- If the preview does not have the token yet, ask the owner to enter it through the UI; do not invent a token or change authentication to bypass it.
- Local backend development is separate from the hosted preview. A local `.env` may be used privately; never commit it. The Gemini key is optional for local runs if using the documented Ollama fallback.

<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Secrets / credentials (READ FIRST)

> [!IMPORTANT]
> **Do NOT ask the user for a Gemini API key.** `GEMINI_API_KEY` is already
> stored permanently as an environment variable on the Render service
> `nous-ai-os` and is used server-side only. The frontend never needs it.
>
> The only credential you need is the **NOUS token** (ask the user for it).
> Use it against the deployed backend:
>
> - API base: `https://nous-ai-os-api.onrender.com`
> - Header: `Authorization: Bearer <NOUS_TOKEN>` (or `X-NOUS-TOKEN`)
> - Frontend: paste it in the dashboard token field. Do not set the token through a `VITE_*` variable: Vite-exposed variables can be embedded in the public frontend bundle.
>
> If you must run the Python backend locally, `GEMINI_API_KEY` is optional:
> leave it empty and AI calls fall back to local Ollama (`NOUS_LOCAL_LLM=1`)
> or test against the Render backend instead. Never commit any key.

## Notes

- TS uses standard `strict` (no noUncheckedIndexedAccess/exactOptionalPropertyTypes) — imported code wasn't written for them.
- The web client always calls the Render backend directly (`src/lib/nous-api.ts`); never route dashboard API calls through a same-origin relative path such as `/api/nous`, because preview and static hosts answer HTML there. The Vite `/api/nous` proxy stays only as a legacy local fallback.
- Cross-site browser calls are accepted from origins in `NOUS_CORS_ORIGINS` plus any `https://*.lovable.app`, `https://*.lovableproject.com` or `https://*.lovable.dev` preview/published app (see `ALLOWED_ORIGIN_SUFFIXES` in `executor/router.py`); auth still requires the NOUS token.
- Python cloud deploy: gunicorn on `$PORT` (Procfile), `render.yaml` with persistent `/app/data` disk.

- Route modules retain route definitions and metadata; page and shell components live in component-only modules so Fast Refresh has valid boundaries.
- Dashboard views, navigation, connection settings and chat persistence are separate modules; dashboard-owned requests share a cancelling/coalescing hook so independent views preserve one consistent session.
- Render requests share one deadline/retry lifecycle and a request-ID wake tracker; retry only GET once on gateway failures, never automatically replay mutations, and schedule mission polls after completion to avoid cold-start overlap.
- UI component modules export only components and types; shared variants and context hooks have separate modules to preserve Fast Refresh without lint exemptions.
- Use Vite native TypeScript path resolution; the compatibility helper removes the wrapper legacy resolver and normalizes Nitro output options until upstream supports Vite 8 cleanly.
- Let TanStack Start derive router basepath from Vite base; keep the local Render proxy serve-only so static subpath builds and previews share correct routes.
- Chat sessions have dedicated route-derived IDs and isolated browser records; remount the dashboard on session changes to cancel prior work.
- Missions and queue snapshots share SQLite transactions with explicit claim records; import legacy JSON once and retain it as backup, never read it as live state after migration.
- Knowledge ingestion exposes persisted processing state and uses the existing local feature-hash cosine search; do not describe it as neural embeddings or add AI providers implicitly.
- Chat tool execution uses a separate read-only allowlist and bounded ReAct loop, never the privileged operational registry; stream execution records once and preserve them after synthesis failures to avoid replay and false completion claims.
- Chat tool cards use AI Elements Tool primitives with concise public action summaries, not private model reasoning; persist terminal records and mark unconfirmed running records interrupted on restoration.
- App Builder Studio owns cancellable per-application requests and a single mutation lock; stream validation output without replay and use authenticated blob downloads.
- Generated-app repairs are review-first: rerun baseline/static checks before explicit application, retain decision status, and never rewrite files during app launch.
- Autonomy enable must be backed by the managed in-process loop (`autonomy_service.start_loop/reconcile`, reconciled at router import); `loop_running` reports the live thread, never the flag, so the UI cannot claim autonomy that is not running.
- Non-diagnostic mission actions live in `executor/mission_actions.py` with per-action payload schemas validated at mission creation; unattended auto-missions may run only its read-only subset, keeping LLM steps and app tests operator-triggered.
- Browser work without Playwright on the host falls back to the guarded HTTP reader/web search and reports `not_available_on_this_host`; interactive actions are never claimed as performed.
- Knowledge memory writes go through the re-entrant file lock + atomic replace with item/size bounds, provenance (`verified: False`) and TTL for web-derived answers, so unverified content ages out.
- Fleet version checks accept a 7+ char Git SHA prefix of a full SHA; release labels still compare exactly.
- GitHub operator results pass through `redact_secrets`, report token presence/source but never values, refuse write actions without a token before any network call, and publish only allowlisted non-secret files; tests mock all GitHub traffic so no real token is ever needed or logged.
- Field/Larmor workspace uses existing authenticated Render endpoints and bounded contextual conversations; calculations use explicit unit conversion and AI interpretations never count as verified detections.
- External schedulers call `POST /remote/service/cycle` (`autonomy_service.external_tick`), which realigns the loop and runs a cycle only when the interval has elapsed, so frequent wake-up pings never multiply work; fresh-disk autonomy enablement is opt-in via `NOUS_AUTONOMY_ENABLED_DEFAULT`.
- Android companion `available` requires both the pairing token and an Android host (`am` on PATH); a Render server can never drive the phone, so the UI must not imply otherwise.
