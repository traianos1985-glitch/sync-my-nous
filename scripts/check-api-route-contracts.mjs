import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const apiClientPath = "src/lib/nous-api.ts";
const apiClient = readFileSync(apiClientPath, "utf8");
const match = apiClient.match(/const FRONTEND_API_PREFIXES = \[([\s\S]*?)\] as const;/);

if (!match) {
  console.error(`Could not find FRONTEND_API_PREFIXES in ${apiClientPath}.`);
  process.exit(1);
}

const configuredPrefixes = [...match[1].matchAll(/["'](\/api\/[^"']+)["']/g)].map(
  (entry) => entry[1],
);
const requiredPrefixes = [
  "/api/approvals",
  "/api/audit",
  "/api/evaluation",
  "/api/feedback",
  "/api/jobs",
  "/api/knowledge",
  "/api/missions",
  "/api/observability",
  "/api/security-audit",
  "/api/security-lessons",
  "/api/status",
  "/api/tools/execute",
  "/api/chat/stream",
];
const configuredSet = new Set(configuredPrefixes);
const requiredSet = new Set(requiredPrefixes);
const errors = [];

for (const prefix of requiredPrefixes) {
  if (!configuredSet.has(prefix)) {
    errors.push(`Missing same-origin API prefix: ${prefix}`);
  }

  const routeName = prefix.replace(/^\/api\//, "").replaceAll("/", ".");
  const routeFile = join("src", "routes", `api.${routeName}.ts`);
  if (!existsSync(routeFile)) {
    errors.push(`Missing TanStack route file for ${prefix}: ${routeFile}`);
  }
}

for (const prefix of configuredPrefixes) {
  if (!requiredSet.has(prefix)) {
    errors.push(`Unexpected frontend API prefix: ${prefix}`);
  }
}

if (configuredSet.size !== configuredPrefixes.length) {
  errors.push("Duplicate FRONTEND_API_PREFIXES entry.");
}

if (errors.length) {
  console.error("API route contract check failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `API route contract check passed (${requiredPrefixes.length} same-origin route prefixes).`,
);
