#!/data/data/com.termux/files/usr/bin/bash
pkg update -y
pkg install -y git python termux-api
git clone git@github.com:traianos1985-glitch/Nous-AI-OS.git
cd Nous-AI-OS
pip install -r requirements.txt
python -m executor.router
