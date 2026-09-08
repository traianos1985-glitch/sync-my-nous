#!/bin/bash
# ============================================================
# NOUS AI OS — Απομακρυσμένη Πρόσβαση μέσω ngrok (Mac/Linux)
# Χρήση: bash deploy/remote_access/setup_ngrok_mac_linux.sh
# ============================================================

echo ""
echo "=========================================="
echo "  NOUS — Απομακρυσμένη Πρόσβαση (ngrok)"
echo "=========================================="
echo ""

# Έλεγχος ngrok
if ! command -v ngrok &>/dev/null; then
    echo "❌ Το ngrok δεν βρέθηκε."
    echo ""
    echo "Εγκατάσταση:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install ngrok/ngrok/ngrok"
        echo "  ή: https://ngrok.com/download"
    else
        echo "  curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc"
        echo "  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
        echo "  sudo apt update && sudo apt install ngrok"
    fi
    echo ""
    echo "Μετά την εγκατάσταση:"
    echo "  1. Φτιάξε δωρεάν λογαριασμό: https://ngrok.com"
    echo "  2. Τρέξε: ngrok config add-authtoken YOUR_TOKEN"
    echo "  3. Ξανατρέξε αυτό το script"
    exit 1
fi

echo "ℹ️  Βεβαιώσου ότι ο NOUS τρέχει (bash deploy/local_mac_linux/start_nous.sh)"
echo ""
echo "🚀 Εκκίνηση ngrok tunnel → port 5000..."
echo ""
echo "============================================"
echo "  Μόλις δεις 'Forwarding https://...':"
echo "  ▸ Αντέγραψε το URL"
echo "  ▸ Άνοιξέ το από το κινητό σου"
echo "  ▸ Έχεις πλήρη πρόσβαση στον NOUS!"
echo "============================================"
echo ""

ngrok http 5000
