import { afterEach, describe, expect, it } from "bun:test";
import {
  canWriteToGithub,
  describeGithubError,
  githubTokenState,
  previewSandboxAppDeploy,
} from "../src/components/nous/github-operator-model";

const FAKE_GH = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4";
const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

describe("GitHub token state", () => {
  it("reports missing token when the backend has none configured", () => {
    const status = { ok: true, connected: false, error: "missing_token", token_configured: false };
    expect(githubTokenState(status)).toBe("missing");
    expect(canWriteToGithub(status)).toBe(false);
  });

  it("reports an invalid token separately from a missing one", () => {
    expect(githubTokenState({ ok: false, connected: false, error: "invalid_credentials" })).toBe(
      "invalid",
    );
  });

  it("allows commits and Pages publishing only when connected", () => {
    expect(canWriteToGithub({ ok: true, connected: true, login: "me" })).toBe(true);
    expect(canWriteToGithub(null)).toBe(false);
    expect(canWriteToGithub({ ok: false, connected: false, error: "network_error" })).toBe(false);
  });
});

describe("GitHub error text", () => {
  it("maps missing_token to a clear instruction", () => {
    expect(describeGithubError("missing_token")).toContain("Λείπει GitHub Token");
  });

  it("never shows GitHub tokens or bearer values", () => {
    const text = describeGithubError(null, `failed: Bearer ${FAKE_GH} raw ${FAKE_GH}`);
    expect(text).not.toContain(FAKE_GH);
    expect(text).toContain("[REDACTED]");
  });
});

describe("Pages deploy preview", () => {
  it("always sends dry_run: true", async () => {
    let sent: unknown = null;
    globalThis.fetch = (async (_url: string, init?: RequestInit) => {
      sent = JSON.parse(String(init?.body));
      return new Response(JSON.stringify({ ok: true, dry_run: true, files: ["index.html"] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as typeof fetch;
    const res = await previewSandboxAppDeploy({ app_name: "demo" });
    expect(sent).toEqual({ app_name: "demo", dry_run: true });
    expect(res.files).toEqual(["index.html"]);
  });
});
