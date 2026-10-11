# Sync My Nous

Το project περιλαμβάνει το Sync My Nous frontend και το Nous AI OS backend.
Το frontend διατηρεί τα υπάρχοντα routes και UI χαρακτηριστικά, ενώ το backend
βρίσκεται στο `nous-ai-os/` ως ανεξάρτητο Python/Flask service.

## Αρχιτεκτονική και deployment

- **Frontend:** Vite/TanStack εφαρμογή, με npm και `package-lock.json` ως το μοναδικό JavaScript package manager/lockfile.
- **Static frontend:** GitHub Pages workflow.
- **Backend API:** το υπάρχον Render service `nous-ai-os`, στο `https://nous-ai-os-api.onrender.com`.
- **Secrets:** το `GEMINI_API_KEY` παραμένει στο Render backend. Οι agents χρησιμοποιούν το NOUS token· δεν ενσωματώνουμε API keys ή master tokens στο frontend.
- **Lovable:** το repository συνεχίζει να συγχρονίζεται με το υπάρχον Lovable project. Οι αλλαγές σε manifests δεν αλλάζουν το Lovable project ή τη σύνδεσή του.

## Κλειδιά (για agents και developers)

- Το `GEMINI_API_KEY` είναι ήδη αποθηκευμένο στο Render (service `nous-ai-os`). Μην το ζητάς και μην το κάνεις commit.
- Χρειάζεσαι μόνο το NOUS token για σύνδεση στο `https://nous-ai-os-api.onrender.com`.
- Τοπικά, το Gemini key είναι προαιρετικό (fallback σε τοπικό Ollama).

## Nous AI OS backend

```sh
cd nous-ai-os
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m executor.router
```

Το `.env` είναι μόνο για τοπική ανάπτυξη. Τα runtime δεδομένα (`nous-ai-os/data/`) και τα secrets παραμένουν εκτός Git.
Για τις οδηγίες API, ασφάλειας και deployment δες το [`nous-ai-os/README.md`](nous-ai-os/README.md).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/1fa033ea-3834-40b6-aaeb-011deabdf812).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone https://github.com/traianos1985-glitch/sync-my-nous.git
cd sync-my-nous
npm ci
npm run dev
```

Run the frontend checks with `npm run check`. Run the backend tests with `npm run test:python`.
