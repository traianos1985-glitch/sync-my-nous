# NOUS Fleet Synchronization and Controlled Rollouts

This package adds request-driven heartbeats, central version-drift detection, a durable rollout queue, and an opt-in scheduled controller. It does not execute shell commands on remote installations or attempt to bypass hosting-provider lifecycle limits.

## What happens automatically

1. A backend installation with the fleet client configured reports its instance ID, provider, deployed commit/version, and coarse status after a normal request completes. HTTP 5xx responses report `degraded`; other completed responses report `healthy`. Identical statuses are throttled to one per process every five minutes, while a status transition is sent immediately. The client does not create a permanent background thread, so it is compatible with serverless/request-driven runtimes.
2. The central coordinator records the metadata and compares the reported version with `NOUS_FLEET_TARGET_VERSION`.
3. A scheduled GitHub Actions workflow calls the coordinator every 15 minutes. The coordinator queues only fresh, outdated instances with an explicit, enabled provider mapping.
4. At most one queued deployment request is dispatched per reconciliation. Duplicate requests for the same instance/release are deduplicated. Provider responses are recorded as `requested` or `failed`; `requested` means the provider accepted the trigger, not that the new release is already healthy.
5. A later heartbeat must report the desired release and `healthy` status before a requested rollout job becomes `converged`. A degraded report blocks the job and prevents further canary expansion. This is a liveness/convergence signal from the running application, not a full dependency or synthetic-transaction health check.
6. Failed requests are retried after a 15-minute cooldown; accepted triggers are retried after 30 minutes if the instance still reports drift. Retries are capped at three attempts per instance/release.

## Endpoints

- `POST /api/agent-environments/fleet/heartbeat` — backend-only authenticated metadata report.
- `GET /api/agent-environments/fleet/status` — administrator-only fleet inventory and version drift.
- `GET /api/agent-environments/fleet/rollout/status` — administrator-only rollout queue and outcomes.
- `POST /api/agent-environments/fleet/rollout/reconcile` — administrator token or dedicated rollout token; queues drift and dispatches at most one configured provider trigger.

## Configure the central coordinator

On the stable coordinator (for example, the existing Render backend):

- `NOUS_FLEET_TOKEN`: high-entropy shared secret for heartbeat requests.
- `NOUS_FLEET_ROLLOUT_TOKEN`: separate high-entropy secret used only by the scheduled rollout controller.
- `NOUS_FLEET_DB_PATH`: point to the SQLite file on the coordinator's persistent disk, e.g. `/var/data/nous_fleet.sqlite3`.
- `NOUS_FLEET_TARGET_VERSION`: exact Git commit SHA intended for all installations. Use the same release identifier convention on every instance; commit SHAs are recommended when the host exposes them.
- `NOUS_FLEET_AUTO_DEPLOY`: leave unset or `false` until the target mapping has been reviewed. Set to `true` only when you explicitly want the coordinator to trigger deployments.
- `NOUS_FLEET_DEPLOY_TARGETS`: server-side JSON map from stable instance IDs to provider targets, described below.
- `NOUS_FLEET_CANARY_IDS`: optional comma-separated list of 1–10 mapped instance IDs. When set, only these canaries are deployed first; the remaining fleet is not queued until every canary is fresh, reports the target version, and reports healthy. A missing/stale/degraded canary fails closed. Leave unset for the existing one-at-a-time rollout without a canary stage.

Do not use browser-visible `VITE_*` variables for these secrets. Do not commit actual values to Git.

## Configure each backend installation

For each installation that should report status, set these **server-side** variables:

- `NOUS_FLEET_COORDINATOR_URL`: base HTTPS URL of the central backend, without a trailing path.
- `NOUS_FLEET_TOKEN`: same fleet-only secret as the coordinator expects.
- `NOUS_FLEET_INSTANCE_ID`: unique stable ID, such as `nous-render-01`, `nous-vercel-01`, or `nous-lovable-01`.
- `NOUS_VERSION`: optional fallback version if the platform does not expose its deployed commit. If available, the client prefers host-provided commit metadata.

The heartbeat contains only `instance_id`, `provider`, `version`, `commit_sha`, and `status`. The status is a coarse response-based liveness signal: HTTP 5xx marks the instance degraded, while other completed responses mark it healthy. It is not a dependency check or synthetic transaction and can miss failures that do not produce a 5xx response. It never sends prompts, missions, user data, environment variables, or API keys. If the coordinator is unavailable, the local NOUS request continues; the client uses a bounded network timeout and retries on later traffic.

A dormant instance cannot report until its host runs it again. This design does not keep sleeping/free-tier instances awake and does not promise heartbeats from a suspended service.

## Provider deployment mappings

Only explicitly enabled and supported targets are dispatched. The mapping is JSON stored in the coordinator's environment, not in the repository. Example shape (replace all example IDs):

```json
{
  "nous-render-01": {
    "provider": "render",
    "service_id": "srv_REPLACE_WITH_REAL_ID",
    "enabled": true
  },
  "nous-vercel-01": {
    "provider": "vercel",
    "deploy_hook_url": "https://api.vercel.com/v1/integrations/deploy/REPLACE_WITH_PROJECT/REPLACE_WITH_HOOK",
    "enabled": true
  }
}
```

- Render deployments use the coordinator's `RENDER_API_KEY` and the mapped Render service ID.
- Vercel deployments use a Vercel deploy-hook URL created in Vercel for the intended project and production branch. The URL is a secret; store it only in the coordinator environment. The controller accepts only HTTPS URLs on `api.vercel.com` with the deployment-hook path.
- Each mapping must use the same instance ID and provider reported by that instance.
- Unknown providers and unmapped instances are not deployed. The controller never accepts a deployment URL from a heartbeat, never runs arbitrary commands, and never embeds provider credentials in the UI.

## Git-connected installations (Lovable and similar)

Where a platform is connected to this GitHub repository and is configured to deploy/sync from `main`, merging an approved PR remains the source of truth and the platform's native Git integration should publish that commit. Configure the stable instance ID and heartbeat variables so the coordinator can verify convergence. This PR does not claim an unsupported public deployment API for Lovable; a Lovable deployment hook/API can be added only if the project has an actual supported, authorized trigger. Until then, it is monitored for drift, and its native Git sync must be configured correctly.

## Enable the scheduled controller

In GitHub repository Settings → Secrets and variables → Actions, add:

- `NOUS_FLEET_COORDINATOR_URL`: the central backend's HTTPS base URL.
- `NOUS_FLEET_ROLLOUT_TOKEN`: the same value configured as a secret on the coordinator.

The workflow `.github/workflows/nous-fleet-rollout.yml` runs every 15 minutes and can also be run manually. If these GitHub secrets are missing, it exits safely without a deployment request. The central backend must also have `NOUS_FLEET_AUTO_DEPLOY=true` and valid target mappings; otherwise reconciliation is report-only.

## Safety and operational boundaries

- This is a one-target-per-run rollout trigger, not a guarantee of zero-downtime or a claim that every host has completed deployment.
- The provider accepting a trigger is recorded as `requested`; convergence is confirmed by subsequent heartbeats and appears as `converged`. Jobs can become `blocked` when a post-deploy heartbeat reports degradation. With `NOUS_FLEET_CANARY_IDS` configured, a failed canary halts expansion. Use `/fleet/status` and `/fleet/rollout/status` to inspect results.
- The queue is persisted alongside the fleet SQLite database and uses a unique instance/release key to avoid duplicate triggers.
- Rollout is opt-in and disabled by default. Keep it disabled until the service IDs, branch targets, credentials, health behavior, and release version are verified.
- The heartbeat status is a lightweight liveness signal and does not replace provider build status, dependency checks, synthetic requests, or rollback. This package halts canary expansion when a canary reports degraded but does not claim automatic provider rollback.
- GitHub Actions scheduling is best-effort and may be delayed by GitHub. Provider rate limits, sleeping instances, build quotas, and security policies remain in force.
