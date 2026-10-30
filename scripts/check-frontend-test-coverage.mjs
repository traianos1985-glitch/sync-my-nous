import { readdirSync, readFileSync } from "node:fs";

const pkg = JSON.parse(readFileSync("package.json", "utf8"));
const scripts = pkg.scripts ?? {};
const reachable = new Set();
const pending = ["check"];

while (pending.length) {
  const name = pending.pop();
  if (reachable.has(name)) continue;
  if (typeof scripts[name] !== "string") {
    console.error(`Frontend check references missing npm script: ${name}`);
    process.exit(1);
  }
  reachable.add(name);
  const dependencies = scripts[name].matchAll(/npm run ([a-zA-Z0-9:_-]+)/g);
  for (const match of dependencies) pending.push(match[1]);
}

const testFiles = readdirSync("scripts").filter(
  (name) => name.endsWith(".test.ts") ||
    name.endsWith(".test.js") ||
    name.endsWith(".test.mjs"),
);
const missing = testFiles.filter(
  (file) => ![...reachable].some((name) => scripts[name].includes(`scripts/${file}`)),
);

if (missing.length) {
  console.error("Frontend test files are not reachable from npm run check:");
  for (const file of missing) console.error(`- scripts/${file}`);
  process.exit(1);
}

console.log(
  `Frontend test coverage contract passed: all ${testFiles.length} scripts/*.test.* files are included in npm run check.`,
);
