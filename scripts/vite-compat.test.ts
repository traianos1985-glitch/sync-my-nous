import { test } from "node:test";
import { deepStrictEqual } from "node:assert";
import { normalizeNitroOutput, withoutLegacyPaths } from "./vite-compat.ts";
import type { UserConfig } from "vite";

test("native paths replace only the wrapper's legacy resolver", () => {
  const react = { name: "vite:react" };
  const nitro = { name: "nitro:init" };
  deepStrictEqual(withoutLegacyPaths([react, [{ name: "vite-tsconfig-paths" }, nitro]]), [
    react,
    nitro,
  ]);
});

test("split Nitro output drops the conflicting deprecated false option", () => {
  const groups = { groups: [{ name: "vendor" }] };
  const output = { inlineDynamicImports: false, codeSplitting: groups };
  normalizeNitroOutput({
    environments: { nitro: { build: { rolldownOptions: { output } } } },
  } as UserConfig);
  deepStrictEqual(output, { codeSplitting: groups });
});

test("inlined Nitro output stays a single bundle", () => {
  const output = { inlineDynamicImports: true, codeSplitting: { groups: [] } };
  normalizeNitroOutput({
    environments: { nitro: { build: { rolldownOptions: { output } } } },
  } as UserConfig);
  deepStrictEqual(output, { codeSplitting: false });
});
