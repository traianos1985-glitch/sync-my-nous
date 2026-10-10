# NOUS runtime hardening notes

- Brain backups discover JSON runtime state under `data/` instead of relying only on a fixed list.
- `data/api_tokens.json`, backup archives, and restore safety archives are excluded from brain backups.
- Restore accepts only canonical `.json` paths under `data/`, validates JSON, checks archive/manifest integrity, rejects duplicate entries, blocks traversal, and enforces size limits. SHA-256 in the manifest detects corruption; it is not a digital signature against a maliciously rewritten manifest.
- App Builder validates every generated path before writing, rejecting absolute paths, traversal, Windows-style paths, duplicate targets, and symlink escapes.
- The Render container uses one Gunicorn worker because the app starts in-process background loops. Increase worker count only after moving those loops to a dedicated process or adding cross-process locking.
- The existing root `.github/workflows/nous-ci.yml` already runs frontend checks and backend tests. The nested workflow was not discoverable by GitHub Actions and has been removed.

## Scope and remaining deployment check

These changes do not modify the NOUS token model, Gemini key configuration, or agent authentication. Backups cover JSON state under `data/`; they do not make arbitrary files outside `data/` persistent on Render. Test app generation and static serving before moving generated app directories onto the Render disk.
