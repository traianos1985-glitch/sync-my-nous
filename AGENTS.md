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
- TS uses standard `strict` (no noUncheckedIndexedAccess/exactOptionalPropertyTypes) — imported code wasn't written for them.
- Dev proxy forwards only `/api/nous/*` to the Python backend; `/api/*` belongs to TanStack server routes.
- Python cloud deploy: gunicorn on `$PORT` (Procfile), `render.yaml` with persistent `/app/data` disk.
