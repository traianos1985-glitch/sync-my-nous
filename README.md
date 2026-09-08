# Sync My Nous

Το project περιλαμβάνει το αρχικό Sync My Nous frontend και το Nous AI OS backend.
Το frontend διατηρεί όλα τα υπάρχοντα routes και UI χαρακτηριστικά, ενώ το backend
έχει ενσωματωθεί στο `nous-ai-os/` ως ανεξάρτητο Python/Flask workspace.

## Nous AI OS backend

```sh
cd nous-ai-os
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m executor.router
```

Τα runtime δεδομένα (`nous-ai-os/data/`) και τα secrets παραμένουν εκτός Git.
Για τις οδηγίες API, ασφάλειας και deployment δες το [`nous-ai-os/README.md`](nous-ai-os/README.md).


This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/1fa033ea-3834-40b6-aaeb-011deabdf812).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
