# NOUS Runtime Health Verification

This check verifies a deployment after an operator has deployed or restarted NOUS. It is deliberately **manual** (`workflow_dispatch`): it does not poll on a schedule, keep a sleeping service awake, restart a provider, or attempt to bypass quotas and lifecycle policies.

## Configure

1. In the repository's GitHub Settings, open **Secrets and variables → Actions → New repository secret**.
2. Add `NOUS_HEALTHCHECK_URL` with the HTTPS base URL of the deployed NOUS backend (for example, the service origin; do not append `/api/system/health`). Do not include credentials, query parameters, or fragments.
3. Open **Actions → NOUS Runtime Health Verification → Run workflow** after a deployment or recovery action.

The workflow makes one bounded GET request to each endpoint:

- `/api/system/health` must return a successful response with `status: healthy` and `kind: liveness`.
- `/api/system/ready` must return a successful response with `ok: true`.

Each request has an eight-second timeout, reads at most 64 KiB, sends no authentication header, exposes only a small redacted result, and is not retried. A failing readiness check fails the workflow even when the process is alive.

## What this proves—and what it does not

A passing run proves that the configured URL responded at that moment and reported ready. It does not prove permanent uptime, durable storage across a restart, backup integrity, or that a platform will never sleep. GitHub Actions scheduling is intentionally not used as a keep-alive mechanism. Continuous operation requires a provider-supported service/restart policy and separately verified persistent storage. Any future automated recovery should use documented provider APIs, bounded retry budgets, cooldowns, audit logs, and explicit production authorization.
