#!/usr/bin/env bash
set -euo pipefail

BACKUP="${1:?Usage: bash restore_data.sh /path/to/nous_backup.tar.gz}"
NOUS_DIR="${NOUS_DIR:-/opt/nous}"

case "$BACKUP" in
  *.tar.gz) ;;
  *) echo "Backup must be a .tar.gz archive" >&2; exit 2 ;;
esac

test -s "$BACKUP"
mkdir -p "$NOUS_DIR/data"
tar -tzf "$BACKUP" >/dev/null

timestamp="$(date +%Y%m%d_%H%M%S)"
if [ -d "$NOUS_DIR/data" ] && [ "$(find "$NOUS_DIR/data" -mindepth 1 -print -quit)" ]; then
  mv "$NOUS_DIR/data" "$NOUS_DIR/data.before-restore-$timestamp"
fi
mkdir -p "$NOUS_DIR/data"
tar -xzf "$BACKUP" -C "$NOUS_DIR"

echo "Restore completed. Restart the service with: docker compose up -d"
