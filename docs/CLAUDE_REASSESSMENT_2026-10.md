# Claude reassessment closure ledger — 2026-10

This document records the code-level response to the independent NOUS review and distinguishes verified fixes from architectural limits. A passing unit test is not evidence of a production Android installation test, a tenant-isolation guarantee, or a sandbox.

## Findings and evidence

### C1 — Self-heal command execution boundary

Addressed in prior hardening work; regression coverage is retained. `/api/ops/self-heal/run` accepts only a filename and source text and does not forward caller-supplied commands. `tests/test_agent_ops_security_boundary.py` proves an injected `test_cmd` is ignored and a non-admin cannot invoke the operation.

### H1 — ReAct workspace path containment

Addressed in prior hardening work. ReAct workspace paths are resolved beneath the configured workspace and reject traversal/symlink escapes. Existing chat-ReAct tests cover traversal, private files and failed reads. This is path containment, not an OS-level sandbox.

### H2 — Proxy-aware authentication lockout

Addressed by PR #349. Trusted proxy hops are configurable and lockout keys use the proxy-normalized remote address. Regression tests cover independent forwarded client addresses and direct-mode spoofed headers. The production proxy-hop count must still be confirmed against the actual proxy chain.

### H3 — Authorization scopes and tenancy

Authorization scopes are covered; full tenant isolation is not claimed. The master NOUS token and explicit user/admin API-token scopes are enforced by `security.py` and `api_tokens.py`; token-store corruption fails closed. Existing security tests cover user-vs-admin scope. The current coordinator does not establish a general per-customer data-isolation model; do not market it as multi-tenant isolation.

### H4 — Exported Android command receiver

Code-level controls exist; device-level verification remains separate. The exported receiver requires the pairing secret and checks sender identity on supported Android versions. The repository CI workflow does not build/install the Android companion, so a physical-device or emulator acceptance test is still required before calling this fully closed.

### M1/M2 — Gunicorn worker and background-loop model

Intentional deployment constraint, documented. Render uses one Gunicorn worker because selected schedulers/loops are process-local. Increasing workers without moving loops to a dedicated process or adding cross-process coordination can duplicate work. This PR does not change the worker count.

### M3 — Traversal and generated-code boundaries

Addressed for the audited paths; not a universal sandbox. Existing backup-restore and App Builder path-validation tests reject traversal and unsafe targets. ReAct workspace writes are constrained. Generated-code validation is not equivalent to isolated execution.

### M4 — Durable state integrity and atomic updates

Addressed for the audited stores. API-token and operator-approval stores use locks, temporary files and atomic replacement; Fleet coordination uses SQLite transactions. Integrity tests verify corrupt stores fail closed without overwriting source data. This does not assert every JSON file in the repository is transactional.

### M5 — Truthful execution and test reporting

Addressed in the ReAct and swarm work preceding this PR. ReAct distinguishes pending approval, failed execution and completed inspection; model-driven chat ReAct has bounded tool execution and records actual tool outcomes. Tests cover real tool execution, blocked calls, duplicate prevention and cancellation.

### Frontend test inventory

Hardened in this PR. `npm run check` now runs a coverage-inventory guard that enumerates every `scripts/*.test.*` file and verifies it is reachable from the check-script graph. The UI-model suite remains part of the same check, and the redaction suite is now included too.

### Backend URL and API route alignment

Hardened in this PR. Existing route-contract checks cover GitHub Pages → Flask routing, dashboard routes and Fleet routes. This PR extends the contract to the ReAct and URL-reader endpoints. The API client continues to use the existing Render base URL and NOUS bearer token.

### ReAct operational endpoint

Hardened in this PR. `POST /api/ops/react/run` is admin-gated, requires a JSON object, a non-empty task and an integer `max_steps` from 1–5. Endpoint tests verify denial-before-dispatch and successful bounded dispatch.

### Fetch and verification tool integration

Hardened in this PR. `POST /api/ops/research/read-url` exposes the existing bounded URL reader behind admin scope. It accepts only a bounded URL string and preserves the reader's public-host, content-type, response-size and redirect restrictions.

### Fleet API boundary

Hardened in this PR. Regression tests verify Fleet status requires admin scope and heartbeat ingestion requires Fleet-specific authentication. Existing coordinator/rollout tests continue to cover drift, staleness and rollout convergence.

### Legacy console approval

Hardened in this PR. `executor.approval.ask_approval` no longer calls `input()`; it fails closed with a migration error. The supported path is the durable, expiring, single-use `executor.operator_approval` workflow.

### Kernel approval gate

Existing gate retained and regression-tested. `test_kernel_approval_gate.py` verifies risky tools are not dispatched before approval, approvals must match the action/payload and approved execution is single-use. Shell commands continue to use their dedicated approval workflow.

### App validation runner and sandbox claims

Explicit limitation. Provider preflight is a read-only compatibility estimate. It does not provision an isolated sandbox or prove generated code safe to execute. Do not describe it as a sandbox.

## Deployment invariants preserved

- No change to the NOUS token onboarding contract.
- No change to the Render-held Gemini API key or the requirement that an installation supplies only its NOUS token.
- No change to the Lovable connection or the Render service's single-worker model.
- No automatic production deploy, token rotation, or Fleet rollout is initiated by these changes.

## Acceptance checks required before merge

1. GitHub Actions frontend quality gate passes, including the test inventory, all configured frontend suites, lint, typecheck, build, public-bundle scan and API route contracts.
2. GitHub Actions Python quality gate passes, including compileall, Ruff, dependency check and the full pytest suite.
3. Gitleaks and formatting checks pass.
4. Vercel preview check is green where configured; a platform build-rate-limit failure is not a code pass.
5. Render deploy for the merged commit is live and `/health` returns HTTP 200.
6. Android receiver behavior remains subject to Android device/emulator acceptance; this CI run alone cannot close it.

## Reassessment guidance

The next independent review should challenge the residual boundaries above: actual trusted proxy hop count, cross-customer isolation expectations, Android exported-receiver behavior on supported Android releases, process-local scheduler behavior on Render, and the fact that provider preflight is not a sandbox. A clean CI run is necessary, not sufficient, for those deployment-level claims.
