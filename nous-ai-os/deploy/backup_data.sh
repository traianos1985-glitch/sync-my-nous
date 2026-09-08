#!/bin/bash
# ============================================================
# NOUS AI OS — Data Backup (τρέξε τοπικά για να κατεβάσεις data)
# Χρήση: bash backup_data.sh user@your-vps-ip
# ============================================================

VPS="${1:-root@YOUR_VPS_IP}"
NOUS_DIR="/opt/nous"
BACKUP_NAME="nous_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "📦 Δημιουργία backup από $VPS..."

ssh "$VPS" "cd $NOUS_DIR && tar czf /tmp/$BACKUP_NAME data/ --exclude=data/brain_backups"
scp "$VPS:/tmp/$BACKUP_NAME" "./$BACKUP_NAME"
ssh "$VPS" "rm /tmp/$BACKUP_NAME"

echo "✅ Backup αποθηκεύτηκε: $BACKUP_NAME"
