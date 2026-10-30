import { readFileSync, readdirSync } from "node:fs";

const apiClient = readFileSync("src/lib/nous-api.ts", "utf8");
const dashboard = readFileSync("src/components/nous/use-dashboard.ts", "utf8");
const flaskDashboardApi = readFileSync("nous-ai-os/executor/dashboard_api.py", "utf8");
const flaskRouter = readFileSync("nous-ai-os/executor/router.py", "utf8");
const fleetBlueprint = readFileSync(
  "nous-ai-os/executor/blueprints/agent_environments_bp.py",
  "utf8",
);
const sectionConfigs = readFileSync("src/components/nous/section-configs.ts", "utf8");
const opsBlueprint = readFileSync("nous-ai-os/executor/blueprints/agent_ops_bp.py", "utf8");
const errors = [];

function requireMatch(source, pattern, message) {
  if (!pattern.test(source)) errors.push(message);
}

// GitHub Pages is static hosting: requests must go to the configured Flask API,
// never to TanStack server handlers on the Pages origin.
requireMatch(
  apiClient,
  /function requestUrl\(path: string\): string \{[\s\S]*?return `\$\{apiBase\}\$\{resolvePath\(path\)\}`;/,
  "Dashboard requests must always use the configured Flask API base URL.",
);
if (/FRONTEND_API_PREFIXES|isFrontendApiPath/.test(apiClient)) {
  errors.push("Do not route dashboard API calls to same-origin TanStack server handlers.");
}

const expectedPathMappings = {
  '"/api/chat": "/chat"': "chat must retain the Flask /chat compatibility mapping",
  '"/api/health": "/health"': "health must retain the Flask /health compatibility mapping",
};
for (const [mapping, message] of Object.entries(expectedPathMappings)) {
  if (!apiClient.includes(mapping)) errors.push(`Missing API path mapping: ${message}.`);
}

// These are the dashboard endpoints actually implemented by the Flask service.
// Keep this contract in sync with dashboard_api.py and router.py.
const dashboardApiRoutes = [
  "/status",
  "/knowledge",
  "/evaluation",
  "/feedback",
  "/audit",
  "/jobs",
  "/approvals",
  "/tools/execute",
  "/security-audit",
];
for (const route of dashboardApiRoutes) {
  if (!flaskDashboardApi.includes(`"${route}"`)) {
    errors.push(`Flask dashboard API is missing route declaration ${route}.`);
  }
}

const routerRoutes = [
  ['@app.route("/chat", methods=["POST"])', "chat"],
  ['@app.route("/health")', "health"],
  ['@app.route("/remote/missions")', "mission list"],
  ['@app.route("/remote/metrics")', "runtime metrics"],
  ['@app.route("/remote/lessons/list")', "lesson list"],
];
for (const [route, label] of routerRoutes) {
  if (!flaskRouter.includes(route)) errors.push(`Flask router is missing the ${label} route.`);
}

// The dashboard must poll the Flask JSON endpoint; an SSE handler does not run on Pages.
requireMatch(
  dashboard,
  /nousFetch<[\s\S]{0,500}?>\s*\("\/remote\/missions"\)/,
  "Mission updates must poll the authenticated Flask /remote/missions endpoint.",
);
if (dashboard.includes('nousStream("/api/missions/stream")')) {
  errors.push("Mission updates must not call the unavailable same-origin SSE route.");
}
requireMatch(
  dashboard,
  /missionPollRef\.current = window\.setTimeout\([\s\S]{0,400}?3_000/,
  "Mission updates must refresh every three seconds while connected.",
);

// Mutating dashboard actions require an admin-scoped token, not just any valid
// user token accepted by the global request guard.
for (const handler of ["api_job_update", "api_approval_resolve", "api_tool_execute"]) {
  const start = flaskDashboardApi.indexOf(`def ${handler}(`);
  const next = start < 0 ? -1 : flaskDashboardApi.indexOf("\n@dashboard_api_bp.", start + 1);
  const body = start < 0 ? "" : flaskDashboardApi.slice(start, next < 0 ? undefined : next);
  if (!body.includes("check_admin_token(request)")) {
    errors.push(`Dashboard mutation handler ${handler} must require an admin token.`);
  }
}

const privilegedRouterHandlers = [
  "tunnel_start_route",
  "tunnel_stop_route",
  "tunnel_save_token_route",
  "backup_route",
  "read_file_route",
  "image_preview_route",
  "remote_nous_drive_approve",
  "remote_nous_drive_reject",
  "remote_executive_run_route",
  "app_builder_run_app_route",
  "app_builder_stop_app_route",
  "larmor_inject_knowledge",
  "inject_guerrilla_knowledge",
  "inject_cache_knowledge",
  "remote_mission_planner_approve",
  "remote_mission_planner_reject",
  "remote_goals_v2_create_mission_route",
];
for (const handler of privilegedRouterHandlers) {
  const start = flaskRouter.indexOf(`def ${handler}(`);
  const next = start < 0 ? -1 : flaskRouter.indexOf("\n@app.route", start + 1);
  const body = start < 0 ? "" : flaskRouter.slice(start, next < 0 ? undefined : next);
  if (!body.includes("check_admin_token(request)")) {
    errors.push(`Privileged router handler ${handler} must require an admin token.`);
  }
}

// Fleet integration controls must stay wired to authenticated Flask endpoints.
requireMatch(
  fleetBlueprint,
  /@agent_environments_bp\.get\("\/fleet\/integrations"\)[\s\S]{0,250}?check_admin_token\(request\)/,
  "Fleet integration status must be exposed through an admin-authenticated Flask endpoint.",
);
for (const route of [
  "/api/agent-environments/fleet/integrations",
  "/api/agent-environments/fleet/status",
  "/api/agent-environments/fleet/rollout/preflight",
  "/api/agent-environments/fleet/rollout/status",
]) {
  if (!sectionConfigs.includes(route)) {
    errors.push(`Control UI is missing fleet endpoint ${route}.`);
  }
}
for (const [route, handler] of [
  ['@agent_ops_bp.route("/react/run", methods=["POST"])', "api_react_run"],
  ['@agent_ops_bp.route("/research/read-url", methods=["POST"])', "api_research_read_url"],
]) {
  const start = opsBlueprint.indexOf(`def ${handler}(`);
  const next = start < 0 ? -1 : opsBlueprint.indexOf("\n@agent_ops_bp.route", start + 1);
  const body = start < 0 ? "" : opsBlueprint.slice(start, next < 0 ? undefined : next);
  if (!opsBlueprint.includes(route) || !body.includes("_admin_required()")) {
    errors.push(`Operational endpoint ${handler} must be registered and require admin scope.`);
  }
}

const packageJson = JSON.parse(readFileSync("package.json", "utf8"));
const npmScripts = packageJson.scripts ?? {};
const reachableScripts = new Set();
const pendingScripts = ["check"];
while (pendingScripts.length) {
  const name = pendingScripts.pop();
  if (reachableScripts.has(name)) continue;
  if (typeof npmScripts[name] !== "string") {
    errors.push(`Frontend check references missing npm script: ${name}`);
    continue;
  }
  reachableScripts.add(name);
  const dependencies = npmScripts[name].matchAll(/npm run ([a-zA-Z0-9:_-]+)/g);
  for (const match of dependencies) pendingScripts.push(match[1]);
}

const frontendTestFiles = readdirSync("scripts").filter((name) =>
  /\.test\.(?:ts|js|mjs)$/.test(name),
);
const missingFrontendTests = frontendTestFiles.filter((file) =>
  [...reachableScripts].every((name) => !npmScripts[name].includes(`scripts/${file}`)),
);
for (const file of missingFrontendTests) {
  errors.push(`Frontend test file is not reachable from npm run check: scripts/${file}`);
}

if (errors.length) {
  console.error("API route contract check failed:");
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log("API route contract check passed (GitHub Pages → authenticated Flask API).");
