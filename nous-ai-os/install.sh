#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y
pkg install -y python git termux-api
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pypdf python-docx Pillow pytesseract
echo "[OK] NOUS installed with document intake support"
