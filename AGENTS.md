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
> - Frontend: paste it in the dashboard token field, or set `VITE_NOUS_API_TOKEN`.
>
> If you must run the Python backend locally, `GEMINI_API_KEY` is optional:
> leave it empty and AI calls fall back to local Ollama (`NOUS_LOCAL_LLM=1`)
> or test against the Render backend instead. Never commit any key.

## Notes

- TS uses standard `strict` (no noUncheckedIndexedAccess/exactOptionalPropertyTypes) — imported code wasn't written for them.
- Dev proxy forwards only `/api/nous/*` to the Python backend; `/api/*` belongs to TanStack server routes.
- Python cloud deploy: gunicorn on `$PORT` (Procfile), `render.yaml` with persistent `/app/data` disk.
