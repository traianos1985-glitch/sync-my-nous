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
- UI component modules export only components and types; shared variants and context hooks have separate modules to preserve Fast Refresh without lint exemptions.
- Use Vite native TypeScript path resolution; the compatibility helper removes the wrapper legacy resolver and normalizes Nitro output options until upstream supports Vite 8 cleanly.
- Let TanStack Start derive router basepath from Vite base; keep the local Render proxy serve-only so static subpath builds and previews share correct routes.
