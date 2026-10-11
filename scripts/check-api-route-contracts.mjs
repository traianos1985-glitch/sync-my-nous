import { readFileSync } from "node:fs";

const apiClient = readFileSync("src/lib/nous-api.ts", "utf8");
const dashboard = readFileSync("src/routes/dashboard.tsx", "utf8");
const flaskDashboardApi = readFileSync("nous-ai-os/executor/dashboard_api.py", "utf8");
const flaskRouter = readFileSync("nous-ai-os/executor/router.py", "utf8");
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
  /missionPollRef\.current = window\.setInterval\([\s\S]{0,400}?3_000/,
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

if (errors.length) {
  console.error("API route contract check failed:");
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log("API route contract check passed (GitHub Pages → authenticated Flask API).");
