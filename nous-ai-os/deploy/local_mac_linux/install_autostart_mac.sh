#!/bin/bash
# ============================================================
# NOUS AI OS — Αυτόματη εκκίνηση σε Mac (launchd)
# Τρέξε: bash deploy/local_mac_linux/install_autostart_mac.sh
# ============================================================

NOUS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.nous.aiOS.plist"

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nous.aiOS</string>
    <key>ProgramArguments</key>
    <array>
        <string>${NOUS_DIR}/venv/bin/python3</string>
        <string>-m</string>
        <string>executor.router</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${NOUS_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OPENROUTER_API_KEY</key>
        <string>$(grep OPENROUTER_API_KEY ${NOUS_DIR}/.env 2>/dev/null | cut -d= -f2)</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/nous.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/nous_err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "✅ Ο NOUS θα ξεκινά αυτόματα κάθε φορά που ανοίγεις τον Mac!"
echo "   URL: http://localhost:5000"
echo "   Logs: tail -f /tmp/nous.log"
echo ""
echo "Για απεγκατάσταση: launchctl unload $PLIST && rm $PLIST"
