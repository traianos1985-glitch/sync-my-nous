# NOUS provider runtime operations

The Agent Environments dashboard is a real, authenticated integration surface, not a claim that every host exposes the same API.

## Implemented operations

- Inventory: bounded runtime/provider detection; environment-variable names and project marker names only. Values are not returned.
- Vercel probe: checks whether the CLI is installed, its version command, and whether vercel whoami succeeds. It returns booleans, not account identity or raw command output.
- Render probe: when RENDER_API_KEY is configured, performs a read-only request to GET /v1/services?limit=1; it returns status and count only.
- Lovable: checks local Git origin configuration for GitHub sync. There is no invented Lovable deployment API.
- Replit/Codespaces: checks runtime markers, workspace availability, and local Git workspace state. It does not assume host account privileges.
- Deployment: Vercel CLI preview or production deployment, and Render service deployment via the Render API. Both require an authenticated NOUS API call and the exact UI/API confirmation phrase DEPLOY.

## Configuration

Set NOUS_WORKSPACE_ROOT to the directory NOUS is allowed to operate in. Without it, the process working directory is the workspace boundary. Project paths are resolved inside that boundary.

For Render, configure RENDER_API_KEY and RENDER_SERVICE_ID in the hosting platform's secret manager. For Vercel, install/authenticate the CLI in the NOUS runtime, or configure a Vercel token for inventory indication. The deployment operation currently uses the authenticated Vercel CLI; a token alone does not silently enable CLI deployment.

Do not put credentials in the repository, UI, diagnostic output, or project files. Rotate credentials if exposed.

## Explicit non-capabilities

A Lovable or Replit marker does not prove access to a provider account. The adapter does not claim projects, change account settings, modify external integrations, or deploy to a provider without the explicit deployment confirmation. Render's service ID refers to the service configured by the owner; the local path is not uploaded to Render by this API operation.

## Agent preview launchpad

The /api/agent-environments/previews endpoint returns safe launch links for StackBlitz, CodeSandbox, v0, Bolt.new, and Railway sandbox documentation. If the configured workspace has a GitHub origin, only the validated owner/repository slug is used to build provider links; remote URLs containing embedded credentials are rejected.

The preview endpoint now also attaches a read-only project compatibility estimate to existing provider cards. It inspects bounded manifests, framework names, lockfiles, and script names, then provides heuristic provider-fit metadata. It does not run project scripts, install dependencies, access the network, or create a sandbox. See [preview project preflight](preview-project-preflight.md) for its request shape and safety limits.

- StackBlitz and CodeSandbox receive direct GitHub import/preview links.
- v0 and Bolt open their official workspace pages and show the detected repository URL for copy/import.
- Railway is documented as an isolated sandbox option, but this UI does not provision a Railway sandbox. Provisioning can consume resources and needs a separately configured, owner-authorized integration.
- Opening a preview provider does not guarantee a successful build; private repositories require provider authorization, and preview behavior depends on framework support.
