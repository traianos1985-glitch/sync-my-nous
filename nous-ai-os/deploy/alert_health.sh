#!/usr/bin/env bash
set -euo pipefail

WEBHOOK_URL="${NOUS_ALERT_WEBHOOK_URL:-}"
MESSAGE="${1:-NOUS health check failed}"

if [[ -z "$WEBHOOK_URL" ]]; then
  printf '%s\n' "$MESSAGE" >&2
  exit 0
fi

curl --fail --silent --show-error --max-time "${NOUS_ALERT_TIMEOUT:-10}" \
  -H 'Content-Type: application/json' \
  --data "$(python -c 'import json,sys; print(json.dumps({"text": sys.argv[1]}))' "$MESSAGE")" \
  "$WEBHOOK_URL" >/dev/null
