#!/bin/bash
# ============================================================
# NOUS AI OS — Αυτόματη εκκίνηση σε Linux Desktop (systemd user)
# Τρέξε: bash deploy/local_mac_linux/install_autostart_linux.sh
# ============================================================

NOUS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

# Φόρτωση API key
API_KEY=$(grep OPENROUTER_API_KEY "${NOUS_DIR}/.env" 2>/dev/null | cut -d= -f2 || echo "")

cat > "$SERVICE_DIR/nous.service" << EOF
[Unit]
Description=NOUS AI OS Personal Server
After=network.target

[Service]
WorkingDirectory=${NOUS_DIR}
ExecStart=${NOUS_DIR}/venv/bin/python3 -m executor.router
Restart=always
RestartSec=5
Environment=OPENROUTER_API_KEY=${API_KEY}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable nous
systemctl --user start nous

echo "✅ Ο NOUS θα ξεκινά αυτόματα!"
echo "   URL: http://localhost:5000"
echo "   Status: systemctl --user status nous"
echo "   Logs:   journalctl --user -u nous -f"
