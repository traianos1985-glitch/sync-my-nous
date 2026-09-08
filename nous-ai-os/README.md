# NOUS AI OS

Αυτόνομος AI agent / «λειτουργικό σύστημα» σε Python + Flask: chat brain, μνήμη,
missions, self-healing, app builder, browser & Android operators, document
intelligence και dashboard, όλα σε ένα service (`executor.router:app`).

## Γρήγορη εκκίνηση

```bash
git clone https://github.com/traianos1985-glitch/Nous-AI-OS.git
cd Nous-AI-OS
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # βάλε το OPENROUTER_API_KEY σου
python -m executor.router   # http://localhost:5000
```

Production:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 executor.router:app
# ή: docker compose up -d
```

## Environment variables

| Variable | Ρόλος |
|---|---|
| `OPENROUTER_API_KEY` | LLM calls (OpenRouter) — **απαραίτητο** για chat/brain |
| `NOUS_TOKEN` | master API token· απαραίτητο για κάθε remote πρόσβαση |
| `NOUS_ALLOW_ANONYMOUS` | `1` = χωρίς auth (μόνο για τοπικές δοκιμές) |
| `NGROK_AUTHTOKEN` | remote tunnel μέσω pyngrok |
| `PORT` | port του dev server (default `5000`) |

Το `.env` φορτώνεται αυτόματα (python-dotenv). Ποτέ μην commitάρεις κλειδιά.

## Ασφάλεια

Το API είναι **fail-closed**: κάθε endpoint εκτός από `/`, `/health`,
`/favicon.ico`, `/robots.txt`, `/static/*`, `/token/*` απαιτεί έγκυρο token
(`X-NOUS-TOKEN` ή `Authorization: Bearer …`). Χωρίς configured token
επιτρέπονται μόνο requests από localhost. Λεπτομέρειες: [SECURITY.md](SECURITY.md).

Δημιουργία token για κινητό/remote χρήση:

```bash
curl -X POST http://localhost:5000/token/create -H "Content-Type: application/json" -d '{"name":"phone"}'
```

## Δομή

```
executor/            ~300 modules: router (Flask API), brain, agents, engines, operators
executor/router.py   το HTTP API (351 routes) + dashboard
executor/auth_guard.py  καθολικός fail-closed έλεγχος token
android_companion/   Android app (Kotlin, accessibility service)
apps/, generated_apps/  εφαρμογές που φτιάχνει ο agent
data/                runtime state (μνήμη, conversations, tokens) — untracked
deploy/              scripts για VPS, Windows/macOS/Linux autostart, ngrok, tailscale
tests/               pytest smoke tests
```

## Development

```bash
pip install pytest ruff
pytest -q          # tests
ruff check .       # lint (σοβαρά σφάλματα)
python -m compileall -q executor
```

Το CI (`.github/workflows/ci.yml`) τρέχει syntax check, ruff, pytest και secret
scan σε κάθε push/PR.

## Runtime data

Ο φάκελος `data/` (conversations, brain state, api tokens) είναι πλέον
untracked: περιέχει προσωπικά δεδομένα και δεν πρέπει να δημοσιεύεται.
Backup: `deploy/backup_data.sh`.
