# NOUS runtime lifecycle planning

The Deploy dashboard exposes `GET /api/agent-environments/lifecycle`. This is
a read-only assessment intended to be the first step of environment-aware
installation and long-lived operation.

## What it assesses

- Provider hints from environment-variable **names** and project marker files.
- Whether the host resembles a serverless/preview runtime, hosted workspace,
  development container, or managed service.
- Persistence hints, without claiming that a volume or database is actually
  durable or reachable.
- A bounded resource snapshot: logical CPU count, a detectable Linux cgroup
  memory limit, and available workspace disk space.
- Deployment integration hints based on installed CLIs and the presence of
  provider credential variable names.
- Recommendations for durable memory, health checks, backups, bounded
  workloads, scoped deployment credentials, and rollback.

## Important limitations

- The endpoint does not read environment values, return secrets, install
  packages, write files, provision infrastructure, or start a keep-alive loop.
- Provider detection is evidence, not proof of account access.
- A marker such as `RENDER_DISK_PATH` or `DATABASE_URL` is only a hint. The
  report cannot prove that a database/volume is reachable, persistent, backed
  up, or restored correctly after a restart.
- Resource availability is a snapshot, not a promise of quota. NOUS should
  use bounded workloads and provider quotas rather than attempting to consume
  all available CPU, memory, disk, or network capacity.
- The report does not perform deployment. Direct deployments remain a separate
  operation, scoped to the configured workspace and subject to authorization.

## Long-lived runtime strategy

Use the preview/editor as the authoring and validation surface. Put the NOUS
control plane, mission scheduler, and persistent memory on a supported managed
service or VPS/container with a documented restart policy, durable database or
volume, health checks, backups, and a tested rollback. Static/serverless
previews should call that backend rather than relying on local preview files
for permanent state.

## Next implementation stages

1. Use this plan during environment bootstrap and present unresolved items as
   explicit readiness blockers.
2. Add a one-time, idempotent preview-deployment workflow for explicitly
   configured providers. It must never promote to production automatically.
3. Verify the deployed preview with health and API smoke tests, record a
   secret-safe result, and stop on failures.
4. Add provider-specific durable-state adapters only where documented APIs and
   credentials are configured; do not pretend Lovable exposes an undocumented
   runtime or deployment API.
5. Add an operator-controlled production promotion and rollback flow.

A platform preview is not a guaranteed permanent process. Continuous operation
must come from the platform's supported service model, not from evading sleep,
quota, lifecycle, or account controls.
