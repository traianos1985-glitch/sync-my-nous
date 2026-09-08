# NOUS AI OS — Deployment Guide

## Επιλογές Hosting

---

### 🏠 Επιλογή Α: Προσωπικός Υπολογιστής (δωρεάν)

Ο NOUS τρέχει στον υπολογιστή σου σαν local server.
Πρόσβαση από browser του ίδιου υπολογιστή **και** από κινητό στο ίδιο WiFi.

#### Windows

**Απαιτήσεις:** Python 3.10+ ([python.org](https://python.org)) — κατά την εγκατάσταση τσέκαρε "Add Python to PATH"

```
1. Κατέβασε το project ως ZIP από Replit
2. Αποσυμπίεσε οπουδήποτε (π.χ. C:\nous-ai-os)
3. Μέσα στον φάκελο, άνοιξε: deploy\local_windows\start_nous.bat
4. Άνοιξε browser: http://localhost:5000
```

**Αυτόματη εκκίνηση με τα Windows:**
```
deploy\local_windows\setup_autostart.bat
```

---

#### Mac

**Απαιτήσεις:** Python3 (συνήθως προεγκατεστημένο — έλεγξε με `python3 --version`)

```bash
# 1. Αποσυμπίεσε το ZIP οπουδήποτε
# 2. Άνοιξε Terminal στον φάκελο
bash deploy/local_mac_linux/start_nous.sh

# Άνοιξε browser: http://localhost:5000
```

**Αυτόματη εκκίνηση κάθε φορά που ανοίγει ο Mac:**
```bash
bash deploy/local_mac_linux/install_autostart_mac.sh
```

---

#### Linux Desktop (Ubuntu, Fedora κ.λπ.)

```bash
sudo apt install python3 python3-pip python3-venv  # Ubuntu/Debian
bash deploy/local_mac_linux/start_nous.sh

# Αυτόματη εκκίνηση:
bash deploy/local_mac_linux/install_autostart_linux.sh
```

---

#### Πρόσβαση από κινητό (ίδιο WiFi)

Όταν τρέχει στον υπολογιστή, ο NOUS είναι προσβάσιμος από **οποιαδήποτε συσκευή στο ίδιο δίκτυο**:

1. Βρες την IP του υπολογιστή σου:
   - Windows: `ipconfig` → IPv4 Address (π.χ. `192.168.1.10`)
   - Mac/Linux: `ifconfig` ή `ip addr`
2. Άνοιξε από το κινητό: `http://192.168.1.10:5000`

> **Σημείωση:** Λειτουργεί μόνο όταν ο υπολογιστής είναι ανοιχτός.
> Για 24/7 online χωρίς να αφήνεις τον υπολογιστή ανοιχτό → δες Επιλογή Β (VPS).

---

### 🌐 Επιλογή Β: VPS (~€4/μήνα, πάντα online)

Ο NOUS τρέχει σε cloud server 24/7 — ανεξάρτητα από τον υπολογιστή σου.

**Καλύτερα providers:**
- **Hetzner Cloud** (EU) — CX22: 2 CPU, 4GB RAM = **€3.79/μήνα** ← συνιστάται
- **DigitalOcean** — Basic 1GB = **$6/μήνα**
- **Vultr** — Cloud Compute 1GB = **$5/μήνα**

**Εγκατάσταση (μία φορά):**
```bash
# Συνδέσου στον server με SSH, μετά:
bash deploy/setup_vps.sh
# Άνοιξε: http://YOUR_SERVER_IP
```

---

### 🐳 Επιλογή Γ: Docker (Windows/Mac/Linux)

Αν έχεις Docker Desktop εγκατεστημένο:
```bash
cp .env.example .env
# Βάλε το OPENROUTER_API_KEY στο .env

docker-compose up -d
# Άνοιξε: http://localhost:5000
```

---

### 🥧 Επιλογή Δ: Raspberry Pi (δωρεάν, τρέχει 24/7 στο σπίτι)

Αν έχεις Raspberry Pi 3/4 — κόστος: **€0/μήνα** (μόνο ρεύμα ~€1-2):
```bash
bash deploy/local_mac_linux/start_nous.sh
# + αυτόματη εκκίνηση:
bash deploy/local_mac_linux/install_autostart_linux.sh
```

---

## Σύγκριση Επιλογών

| | Κόστος | Online 24/7 | Απαιτήσεις |
|---|---|---|---|
| Προσωπικός PC | €0 | Μόνο αν είναι ανοιχτός | Python |
| VPS | ~€4-6/μήνα | ✅ Ναι | Πιστωτική κάρτα |
| Docker | €0 | Μόνο αν είναι ανοιχτός | Docker Desktop |
| Raspberry Pi | ~€1-2/μήνα ρεύμα | ✅ Ναι | Pi + Linux |

---

## Environment Variables (.env)

Δημιούργησε αρχείο `.env` στον κύριο φάκελο:
```
OPENROUTER_API_KEY=sk-or-v1-PUT_YOUR_KEY_HERE
```

---

## Backup & Ενημέρωση

```bash
# Backup μνήμης/goals/συνομιλιών (από VPS):
bash deploy/backup_data.sh root@YOUR_VPS_IP

# Ενημέρωση κώδικα (σε VPS):
bash deploy/update.sh
```
