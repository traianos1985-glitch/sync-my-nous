# NOUS Security Baseline

This document records the security properties enforced by the runtime and the
checks expected before merging runtime changes. It is a baseline, not a claim
that the entire system has undergone an external security audit.

## Authentication and secrets

- Remote routes are protected by the global Flask auth guard unless explicitly
  listed as public or covered by their own authentication mechanism.
- Requests may authenticate with `X-NOUS-TOKEN` or `Authorization: Bearer …`.
- The configured `NOUS_TOKEN` is compared using constant-time comparison.
- Issued API tokens are stored as SHA-256 hashes; the raw token is returned only
  at creation time.
- The token store uses a process/thread lock and atomic file replacement.
  Corrupt or malformed token data fails closed and must not be overwritten
  automatically. Back up and inspect the file before attempting recovery.
- Never commit `.env`, `data/api_tokens.json`, credential files, private keys,
  or live provider keys. Keep provider API keys in the hosting platform's secret
  settings, not in the repository or client-side dashboard.

## Request and response boundaries

- The default request body limit is 16 MiB; deployments that need a different
  upload size should set an explicit, reviewed `MAX_CONTENT_LENGTH`.
- Responses include `nosniff`, frame-denial, and referrer-policy headers.
- API, remote-control, and token endpoints return `Cache-Control: no-store`.
- HTTPS deployments add HSTS when Flask sees the request as secure. Reverse
  proxy configuration must correctly communicate HTTPS status.

## Operational expectations

1. Keep `NOUS_TOKEN` configured for any publicly reachable deployment.
2. Keep `NOUS_ALLOW_ANONYMOUS` disabled outside isolated local development.
3. Rotate a potentially exposed token and revoke the old token immediately.
4. Review GitHub Actions results for Python tests, frontend checks, linting,
   dependency checks, and secret scanning before merging.
5. Treat a failed or unavailable auth store as an incident; do not reset it to
   an empty token list to make the service start.
6. Exercise the dashboard and device/remote-control flows on the actual target
   device before enabling autonomous actions.

## Scope and limitations

The auth guard and these tests do not replace endpoint-specific authorization,
approval checks for dangerous actions, deployment hardening, dependency review,
or a professional penetration test. The request-size limit is a coarse global
bound, not a per-user rate limiter. The NOUS dashboard should remain private
until the deployment configuration and end-to-end behavior have been verified.
