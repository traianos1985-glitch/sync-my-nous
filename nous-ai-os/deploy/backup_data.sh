#!/bin/bash
# ============================================================
# NOUS AI OS — Data Backup (τρέξε τοπικά για να κατεβάσεις data)
# Χρήση: bash backup_data.sh user@your-vps-ip
# ============================================================

VPS="${1:-root@YOUR_VPS_IP}"
NOUS_DIR="/opt/nous"
BACKUP_NAME="nous_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "📦 Δημιουργία backup από $VPS..."

ssh "$VPS" "set -e; cd $NOUS_DIR && test -d data && tar --exclude='data/brain_backups' -czf /tmp/$BACKUP_NAME data/"
scp "$VPS:/tmp/$BACKUP_NAME" "./$BACKUP_NAME"
ssh "$VPS" "rm -f /tmp/$BACKUP_NAME"

test -s "./$BACKUP_NAME"
echo "✅ Backup αποθηκεύτηκε: $BACKUP_NAME"
