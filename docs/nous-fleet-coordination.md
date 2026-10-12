# NOUS Fleet Coordination

NOUS Fleet Coordination is the first control-plane layer for installations deployed to Render, Vercel, Lovable-connected hosting, and other supported environments.

## Architecture

- The configured central backend hosts `/api/agent-environments/fleet/heartbeat` and `/api/agent-environments/fleet/status`.
- Every installation reports a stable `instance_id`, provider ID, version/commit, and coarse health status. Do not send prompts, mission contents, tokens, environment variables, user data, or arbitrary URLs.
- Heartbeats are authenticated with a server-side `NOUS_FLEET_TOKEN`. The token must be stored as a secret in each backend environment; never expose it in a browser build or commit it.
- The registry is stored in SQLite at `NOUS_FLEET_DB_PATH` (or `NOUS_DATA_DIR/nous_fleet.sqlite3`). Configure a persistent Render disk and point `NOUS_FLEET_DB_PATH` at its mount path, such as `/var/data/nous_fleet.sqlite3`. Without persistent storage, registry data can be lost on redeploy/restart.
- Admins query fleet state with the existing admin-scoped NOUS token. Instance IDs are metadata labels, not authentication.

## Configure the initial coordinator

1. Choose the stable Render backend as the coordinator, for example `https://nous-ai-os-api.onrender.com`.
2. Configure a high-entropy `NOUS_FLEET_TOKEN` as a server-side secret on the coordinator and each participating backend installation. Keep it separate from browser-visible `VITE_*` variables.
3. Configure a persistent disk on the coordinator and set `NOUS_FLEET_DB_PATH` to a file on that disk.
4. Set `NOUS_FLEET_TARGET_VERSION` to the exact version or release identifier all installations should converge on.
5. After this PR is deployed, each installation can POST its metadata to `/api/agent-environments/fleet/heartbeat`; use the same fleet secret in `X-NOUS-FLEET-TOKEN`. Admin clients can GET `/api/agent-environments/fleet/status` with the admin token.

Example heartbeat body:

```json
{"instance_id":"nous-vercel-01","provider":"vercel","version":"release-1","commit_sha":"abcdef1234567","status":"healthy"}
```

## Automatic updates: explicit boundary

This first version **registers installations and detects version drift**, but deliberately does not claim to self-update deployments yet. A central coordinator cannot safely redeploy a Vercel or Render service without an explicitly configured provider credential, a mapping from instance IDs to provider project/service IDs, and a rollout/rollback policy. The next stage should add a central, opt-in deployment queue with provider-specific credentials kept only on the coordinator, idempotency keys, canary rollout, post-deploy health verification, cooldowns, and rollback. It must not ask each remote agent to run `git pull`, embed deployment credentials in previews, or bypass platform lifecycle/security controls.

The fleet API does not relay arbitrary commands between instances. It exchanges only version/health metadata and desired-version information.
