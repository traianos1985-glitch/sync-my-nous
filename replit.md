# Running Sync My Nous on Replit

- The frontend uses the `Start application` workflow (`npm run dev`) on port 5000. Vite proxies `/api/nous/*` to the local Python backend.
- The Python/Flask backend uses the `NOUS backend` workflow on port 8000. It
  binds to `0.0.0.0` for workflow port detection and requires `NOUS_TOKEN` for
  remote API access.
- Add `GEMINI_API_KEY` to Replit Secrets to enable Gemini for frontend chat and
  the Python backend's chat, multi-turn, and image requests. The old
  `GCP_API_KEY` name remains supported by the Python backend for existing
  deployments.
- To call the Python API from the dashboard, enter its NOUS API token in the
  dashboard's password field; the browser keeps it in session storage.
- The frontend's Better Auth and database-backed features use Replit's
  `DATABASE_URL` and `SESSION_SECRET`.
- Run `npm run check` for frontend lint/build and `python -m pytest -q nous-ai-os/tests`
  for Python tests.
