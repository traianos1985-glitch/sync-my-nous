import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const publicAssetRoots = [".output/public/assets", "dist/assets"].filter((path) => {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
});

if (publicAssetRoots.length === 0) {
  console.error("No public asset directory found; run the production build before scanning.");
  process.exit(1);
}

const patterns = [
  ["frontend token environment variable", /VITE_NOUS_API_TOKEN/],
  ["NOUS API token", /nous_[A-Za-z0-9_-]{32,}/],
  ["Google API key", /AIza[0-9A-Za-z_-]{30,}/],
  ["OpenAI-style secret key", /sk-(?:proj-)?[A-Za-z0-9_-]{24,}/],
  ["OpenRouter-style secret key", /sk-or-v1-[A-Za-z0-9_-]{20,}/],
];

const findings = [];

function scan(path) {
  const stats = statSync(path);
  if (stats.isDirectory()) {
    for (const entry of readdirSync(path)) scan(join(path, entry));
    return;
  }
  const source = readFileSync(path, "utf8");
  for (const [label, pattern] of patterns) {
    if (pattern.test(source)) findings.push({ path, label });
  }
}

for (const root of publicAssetRoots) scan(root);

if (findings.length > 0) {
  for (const finding of findings) {
    console.error(`Potential ${finding.label} found in public bundle: ${finding.path}`);
  }
  console.error("Refusing to publish a frontend bundle containing token-like material.");
  process.exit(1);
}

console.log(`Public bundle secret scan passed (${publicAssetRoots.join(", ")}).`);
