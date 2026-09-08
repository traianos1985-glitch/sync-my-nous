#!/bin/bash
# ============================================================
# NOUS AI OS — Tailscale VPN Setup (Mac/Linux)
# Tailscale: δωρεάν, ασφαλές VPN — χωρίς port forwarding
# Τρέξε: bash deploy/remote_access/setup_tailscale.sh
# ============================================================

echo ""
echo "=========================================="
echo "  NOUS — Tailscale VPN Setup"
echo "=========================================="
echo ""

if command -v tailscale &>/dev/null; then
    echo "✅ Tailscale είναι ήδη εγκατεστημένο"
else
    echo "[*] Εγκατάσταση Tailscale..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  Για Mac: Κατέβασε από https://tailscale.com/download/mac"
        echo "  ή: brew install --cask tailscale"
        open "https://tailscale.com/download/mac" 2>/dev/null || true
        exit 0
    else
        curl -fsSL https://tailscale.com/install.sh | sh
    fi
fi

echo ""
echo "[*] Σύνδεση στο Tailscale δίκτυο..."
sudo tailscale up

echo ""
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "ανέφικτο")
echo "=========================================="
echo "  ✅ Tailscale ενεργό!"
echo ""
echo "  Η IP του υπολογιστή σου στο Tailscale:"
echo "  http://${TAILSCALE_IP}:5000"
echo ""
echo "  Για πρόσβαση από κινητό:"
echo "  1. Εγκατάστησε το Tailscale app στο κινητό"
echo "  2. Συνδέσου με τον ίδιο λογαριασμό"
echo "  3. Άνοιξε: http://${TAILSCALE_IP}:5000"
echo "=========================================="
