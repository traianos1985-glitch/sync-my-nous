# Roadmap

## Done

- [x] Fix broken build (vite config)
- [x] Home ↔ dashboard link
- [x] Loop: crash-safe cycles + backoff
- [x] API: resilient /overview, `/api/system/metrics`, uptime
- [x] Cloud: Procfile uses PORT/gunicorn, render.yaml, docker port fix
- [x] Dashboard live data from NOUS API (Render URL, token auth, timeout, CORS)
- [x] `nous-api.ts`: always call Render directly; backend accepts Lovable preview origins
- [x] Natural intent understanding + intent wiring + execute actions
- [x] Intent-first routing before browser/search tools
- [x] Full capability awareness + safe tool allowlist
- [x] Approval bridge unify paths + close-loop polish
- [x] Live search + git approval path
- [x] Search relevance scoring + calculator UX
- [x] Low-relevance LLM fallback for weak web hits
- [x] Site-aware product search (official domains for Render/Vercel/…)
- [x] Persistent NOUS auth across preview sessions
- [x] Fleet coordination registry, heartbeats, canary rollout, preflight (opt-in)

## Next

- [ ] Search observability: % low_relevance / % LLM fallback metrics
- [ ] Rate-limit UX: show «Περίμενε ~Xs» as soft wait, not error
- [ ] Intent regression suite (fixed prompts → expected tool)
- [ ] Page-reader + high-score official URLs before pure knowledge fallback
- [ ] CI: clear fast-refresh warnings in dashboard, keep python/frontend green
- [ ] Fleet canary dry-run on one instance without enabling auto-deploy
