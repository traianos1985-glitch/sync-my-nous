#!/usr/bin/env bash
set -euo pipefail

URL="${NOUS_HEALTH_URL:-http://127.0.0.1:5000/health}"
READY_URL="${NOUS_READY_URL:-http://127.0.0.1:5000/ready}"
TIMEOUT="${NOUS_HEALTH_TIMEOUT:-10}"

check() {
  local endpoint="$1"
  curl --fail --silent --show-error --max-time "$TIMEOUT" "$endpoint" >/dev/null
}

if ! check "$URL" || ! check "$READY_URL"; then
  "$(dirname "$0")/alert_health.sh" "NOUS health check failed at $(date -u +%FT%TZ)" || true
  exit 1
fi
printf 'NOUS healthy: %s\n' "$(date -u +%FT%TZ)"
