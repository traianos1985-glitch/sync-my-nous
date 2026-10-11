# NOUS preview project preflight

The authenticated `POST /api/agent-environments/preflight` endpoint estimates which external preview provider is likely to fit a project before the user opens a provider link.

Example request:

```json
{"project_path":"."}
```

The path is resolved inside `NOUS_WORKSPACE_ROOT` (or the process working directory when unset). The response reports detected project types, lockfiles, framework names, script *names*, and heuristic fit/recommendation fields for StackBlitz, CodeSandbox, v0, Bolt.new, and Railway Sandboxes.

## Safety and limitations

- This is read-only static inspection. It does not install dependencies, run project scripts, make network requests, start a provider sandbox, or deploy.
- It reads only bounded, known manifest files (up to 256 KiB each); it does not read `.env` files or application source.
- Script bodies and manifest values are not returned. Python requirements are reduced to package identifiers; private package URLs and credentials are not included in output.
- Manifest symlinks resolving outside the configured workspace are ignored.
- Scores are heuristics, not a promise of build success. Runtime support, private repository authorization, provider account access, required environment variables, and external services can still prevent a preview.
- A provider marked as recommended is not automatically opened or provisioned. User action and any provider-side authorization remain required.
