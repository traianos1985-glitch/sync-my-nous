"""Cloud entrypoint (Render / Railway / Fly / Heroku-style). Reads PORT and HOST."""
import os

from executor.router import app

if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "5000")))
