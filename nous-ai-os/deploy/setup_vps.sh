#!/bin/bash
# ============================================================
# NOUS AI OS — VPS Setup Script
# Δοκιμασμένο σε: Ubuntu 22.04 / 24.04 (Hetzner, DigitalOcean, Vultr)
# Τρέξε ως root: bash setup_vps.sh
# ============================================================

set -e

NOUS_DIR="/opt/nous"
NOUS_USER="nous"
DOMAIN=""   # Αφέτε κενό αν δεν έχετε domain — θα χρησιμοποιηθεί η IP

echo "======================================"
echo "  NOUS AI OS — VPS Εγκατάσταση"
echo "======================================"

# ── 1. System updates ─────────────────────────────────────────
echo "[1/7] Ενημέρωση συστήματος..."
apt-get update -q && apt-get upgrade -y -q

# ── 2. Dependencies ───────────────────────────────────────────
echo "[2/7] Εγκατάσταση dependencies..."
apt-get install -y -q python3 python3-pip python3-venv git curl nginx ufw

# ── 3. Firewall ───────────────────────────────────────────────
echo "[3/7] Ρύθμιση firewall..."
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw allow 5000
ufw --force enable

# ── 4. System user ────────────────────────────────────────────
echo "[4/7] Δημιουργία system user..."
id -u $NOUS_USER &>/dev/null || useradd -m -s /bin/bash $NOUS_USER

# ── 5. Clone + Install ────────────────────────────────────────
echo "[5/7] Κατέβασμα κώδικα..."
mkdir -p $NOUS_DIR
if [ -d "$NOUS_DIR/.git" ]; then
    cd $NOUS_DIR && git pull
else
    # Αντιγραφή από τρέχοντα φάκελο (αν τρέχει τοπικά) ή clone
    if [ -f "./executor/router.py" ]; then
        cp -r . $NOUS_DIR/
    else
        echo "ΣΦΑΛΜΑ: Τρέξε αυτό το script από τον φάκελο NOUS AI OS"
        exit 1
    fi
fi

cd $NOUS_DIR
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt gunicorn

mkdir -p data apps forge executor/plugins

# ── 6. Environment ────────────────────────────────────────────
echo "[6/7] Ρύθμιση environment..."
if [ ! -f "$NOUS_DIR/.env" ]; then
    echo "Βάλε το OpenRouter API key:"
    read -r -p "OPENROUTER_API_KEY: " API_KEY
    cat > $NOUS_DIR/.env << EOF
OPENROUTER_API_KEY=${API_KEY}
EOF
    echo "✅ .env αποθηκεύτηκε"
fi

chown -R $NOUS_USER:$NOUS_USER $NOUS_DIR

# ── 7. Systemd service ────────────────────────────────────────
echo "[7/7] Δημιουργία systemd service..."
cat > /etc/systemd/system/nous.service << EOF
[Unit]
Description=NOUS AI OS
After=network.target

[Service]
User=${NOUS_USER}
WorkingDirectory=${NOUS_DIR}
EnvironmentFile=${NOUS_DIR}/.env
ExecStart=${NOUS_DIR}/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 executor.router:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nous
systemctl start nous

# ── Nginx reverse proxy (port 80) ────────────────────────────
cat > /etc/nginx/sites-available/nous << EOF
server {
    listen 80;
    server_name ${DOMAIN:-_};

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/nous /etc/nginx/sites-enabled/nous
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  ✅ NOUS AI OS εγκαταστάθηκε!"
echo "======================================"
echo ""
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_IP")
echo "  🌐 Άνοιξε: http://${SERVER_IP}"
echo "  📋 Logs:   journalctl -u nous -f"
echo "  🔄 Restart: systemctl restart nous"
echo "  ⏹  Stop:   systemctl stop nous"
echo ""
