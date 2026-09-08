#!/data/data/com.termux/files/usr/bin/bash
pkg update -y
pkg install -y python git termux-api
pip install -r requirements.txt
echo "[OK] NOUS installed"
