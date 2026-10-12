# NOUS Technical Intelligence

## Purpose

The Technical Intelligence service checks the project's declared direct dependencies against their official package registries and produces evidence-linked upgrade recommendations. It is a read-only advisor, not a package manager or autonomous code writer.

## Sources and scope

- npm packages are discovered from the root `package.json`; the current version is read from the root `package-lock.json`.
- Python packages are discovered from `nous-ai-os/requirements.txt` and `nous-ai-os/requirements-dev.txt`. The current version comes from installed distribution metadata when available; if it cannot be determined, the report labels the comparison as unknown instead of inventing a current version.
- npm latest-version metadata comes only from `registry.npmjs.org`.
- Python latest-version metadata comes only from `pypi.org`.
- Requests are HTTPS-only, have bounded timeouts and response sizes, and do not follow redirects. No user-provided URL is fetched by this service.
- Each result includes an official package page URL, the detected current version when available, the latest stable registry version, and a conservative major/minor/patch classification.

## API and dashboard

- `GET /remote/technical-intelligence/status`: last scan, summary, history and safety mode.
- `GET /remote/technical-intelligence/report`: full latest report.
- `GET /remote/technical-intelligence/proposals`: only findings that indicate a possible update.
- `POST /remote/technical-intelligence/scan`: scan declared dependencies. Requires the admin token. JSON body accepts `limit` from 1 through 60; defaults to 40.

The dashboard exposes the same functions under **Tech Watch**. A scan can take several seconds because it checks external registries. If some providers are unavailable, the report is marked `partial` or `unavailable`, and per-package failures are retained.

## Safety boundary

- No package is installed or upgraded.
- No source file is changed.
- No command is executed.
- No code is generated from registry metadata.
- Findings are proposals only. Major-version updates explicitly require review of breaking changes.
- Registry responses are treated as data; package descriptions, release text and other registry-provided text are not used as instructions.

The report is written atomically to the runtime data directory, with a bounded summary history. Runtime storage may be ephemeral on some hosting platforms, so the report is an operational cache, not a durable source of truth.

## CI and supply-chain maintenance

Dependabot is configured separately to propose dependency updates for npm, Python requirements/manifests, and GitHub Actions. Its PRs still require the repository's normal CI and human review; this service never merges or applies them automatically.

## Official technical release intelligence

The separate `technical_sources` watcher checks a fixed allowlist of official GitHub project release APIs (not arbitrary URLs) for recent releases and release-note summaries. The initial allowlist covers Python, Flask, Requests, Vite, and Next.js. Each result records its source URL, release tag, publication time, and a short bounded excerpt.

- The watcher uses HTTPS, a fixed `api.github.com` host, finite timeouts, no redirects, response-size limits, and a small fixed source count.
- Release-note text is untrusted reference material. NOUS stores it as data only; it is not passed to a shell, code interpreter, or automatic patch executor.
- The scan endpoint requires the admin token. Status and report endpoints are read-only.
- A successful scan means sources were queried, not that a recommendation is automatically correct or compatible with the deployed runtime.
- This is a bounded curated-source monitor, not a universal crawler or a claim that every upstream project is watched.

## Upgrade planner execution boundary

The self-upgrade planner is proposal-only. Approving a plan records that it is approved for technical review; it does not call an LLM to generate code, write new source files, or run generated code. Implementation must be made as a separate reviewed source-control change with tests and successful CI. Legacy plans previously marked `implementing` are migrated to the review-only `approved` state when loaded.

## Release evidence triage

- `GET /remote/technical-sources/triage` turns the most recent official-release report into a bounded, deterministic review queue.
- The queue highlights keyword signals for security, breaking changes, bug fixes, and performance. These are triage hints, not a claim that a release is safe, vulnerable, or compatible.
- Each item retains its official release link and bounded excerpt, and is marked as requiring human review. Unknown repositories and arbitrary source links are excluded.
- This step does not create upgrade plans, generate code, edit source files, install packages, or execute release-note content. A future proposal may cite these items, but any implementation must still be a separate reviewed PR with passing CI.

- `POST /remote/technical-sources/propose-upgrades` explicitly creates up to 5 review-only upgrade plans from classified items in the latest triage queue. It requires the normal NOUS token; it is not called by either scan.
- Proposal creation rechecks the fixed official repository allowlist, deduplicates by repository and release tag, retains the source URL and bounded excerpt, and adds a checklist to verify actual project usage, complete release notes, compatibility, and tests.
- A keyword signal is not proof that the upstream project is used by this deployment or that an update is required. The action does not infer affected files, install dependencies, generate code, modify source files, or execute release-note content. Implementation remains a separate reviewed PR with passing CI.

## Hosted-runtime resilience

- Official release-source requests run with a bounded worker pool, so configured per-source timeouts do not add up serially across all sources.
- The report preserves the configured source order and records unexpected worker failures as sanitized per-source errors; successful sources remain usable as partial evidence.
- Release-evidence proposal creation fails explicitly when the source queue is `unavailable` or `not_scanned`. An empty successful HTTP response is not treated as proof that release evidence was retrieved.
- Proposal generation remains review-only; no release text is executed and no dependency or source changes are applied.
