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

## Production monitoring και durable recovery

Το `monitor_health.sh` μπορεί να εκτελείται από cron/systemd timer και να συνδεθεί με alerting service. Τα jobs και τα rate-limit counters αποθηκεύονται στο Neon, ώστε restart ή αλλαγή instance να μη χάνει το lifecycle state.

```bash
chmod +x deploy/monitor_health.sh deploy/alert_health.sh
export NOUS_ALERT_WEBHOOK_URL=https://hooks.example.invalid/nous

`NOUS_ALERT_WEBHOOK_URL` είναι προαιρετικό webhook συμβατό με payload `{ "text": "..." }`. Αν δεν οριστεί, το monitor γράφει το σφάλμα στο stderr και συνεχίζει με exit code 1 για cron/systemd.

Το dashboard χρησιμοποιεί `/api/missions/stream` με authenticated SSE για live mission progress.

chmod +x deploy/monitor_health.sh
*/5 * * * * cd /opt/nous && deploy/monitor_health.sh || logger -t nous-health "NOUS health check failed"
```

Για πραγματικό production authentication, αντικατάστησε το προσωρινό `x-nous-user-id` identity με Better Auth session middleware πριν εκθέσεις τα endpoints δημόσια.

## Ασφαλής συνεχής λειτουργία και ανάκτηση

Ο NOUS μπορεί να τρέχει 24/7 σε VPS ή Docker με `restart: always`, health checks και persistent `data/` volume. Η αυτοβελτίωση είναι σκόπιμα ελεγχόμενη: δεν κατεβάζει και δεν εκτελεί αυθαίρετο remote Python code. Οι ενημερώσεις γίνονται μέσω signed/approved GitHub CI/CD deployment, ώστε να υπάρχει rollback και audit trail.

Για production:

```bash
# στο VPS, μετά το αρχικό setup
cp .env.example .env
# βάλε τα keys και ένα NOUS_VERSION
sudo docker compose up -d --build
sudo docker compose ps
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/ready
```

Χρησιμοποίησε reverse proxy με HTTPS, firewall που επιτρέπει μόνο 80/443 και καθημερινό backup του `data/`. Μην εκθέτεις απευθείας τα management endpoints στο Internet.

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

# Restore με safety snapshot του υπάρχοντος data/:
NOUS_DIR=/opt/nous bash deploy/restore_data.sh ./nous_backup_YYYYMMDD_HHMMSS.tar.gz

# Ενημέρωση κώδικα (σε VPS):
bash deploy/update.sh
```
