#!/bin/bash
# ============================================================
# NOUS AI OS — Local PC Server (Mac / Linux)
# Χρήση: bash deploy/local_mac_linux/start_nous.sh
# ============================================================

NOUS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$NOUS_DIR"

echo ""
echo "=========================================="
echo "  NOUS AI OS — Personal Server"
echo "=========================================="
echo ""

# Έλεγχος Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 δεν βρέθηκε!"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   Εγκατάστησε με: brew install python3"
        echo "   ή από: https://www.python.org/downloads/"
    else
        echo "   Εγκατάστησε με: sudo apt install python3 python3-pip"
    fi
    exit 1
fi

# Έλεγχος ή δημιουργία virtual environment
if [ ! -d "venv" ]; then
    echo "[*] Δημιουργία virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Dependencies
echo "[*] Έλεγχος dependencies..."
pip install -r requirements.txt -q

# Φάκελοι
mkdir -p data apps forge executor/plugins

# Φόρτωση .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Βρες local IP για πρόσβαση από κινητό
LOCAL_IP=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "ανέφικτο")
else
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "ανέφικτο")
fi

echo ""
echo "=========================================="
echo "  ✅ Ο NOUS ξεκινά!"
echo ""
echo "  💻 Από αυτόν τον υπολογιστή:"
echo "     http://localhost:5000"
echo ""
echo "  📱 Από κινητό (ίδιο WiFi):"
echo "     http://${LOCAL_IP}:5000"
echo ""
echo "  ⏹  Για να σταματήσεις: Ctrl+C"
echo "=========================================="
echo ""

python3 -m executor.router
