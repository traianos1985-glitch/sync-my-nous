#!/bin/bash
# ============================================================
# NOUS AI OS — Update Script (τρέξε στον VPS για ενημέρωση)
# ============================================================

NOUS_DIR="/opt/nous"

echo "🔄 Ενημέρωση NOUS AI OS..."

cd $NOUS_DIR

# Backup data
cp -r data data_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Update code (αν χρησιμοποιείς git)
# git pull

# Install new dependencies
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt gunicorn -q

# Restart service
systemctl restart nous
sleep 2

if systemctl is-active --quiet nous; then
    echo "✅ NOUS AI OS ενημερώθηκε και τρέχει κανονικά"
else
    echo "❌ Πρόβλημα — δες: journalctl -u nous -n 50"
fi
