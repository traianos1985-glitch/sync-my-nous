import { nousFetch } from "@/lib/nous-api";
import { redactForAudit } from "@/lib/redaction";

export type GithubStatus = {
  ok: boolean;
  connected: boolean;
  login?: string;
  name?: string;
  avatar_url?: string;
  html_url?: string;
  public_repos?: number;
  total_private_repos?: number;
  scopes?: string[];
  rate_limit_remaining?: number;
  default_owner?: string;
  token_configured?: boolean;
  token_source?: "config" | "env" | "argument" | null;
  message?: string;
  error?: string;
};

export type GithubTokenState = "unknown" | "missing" | "invalid" | "connected" | "error";

/** Derive the GitHub token state shown in the UI; never inspects token values. */
export function githubTokenState(status: GithubStatus | null): GithubTokenState {
  if (!status) return "unknown";
  if (status.connected) return "connected";
  if (status.error === "missing_token" || status.token_configured === false) return "missing";
  if (status.error === "invalid_credentials" || status.error === "github_http_401") return "invalid";
  return "error";
}

/** Commits and Pages publishing require a working token. */
export function canWriteToGithub(status: GithubStatus | null): boolean {
  return githubTokenState(status) === "connected";
}

const GITHUB_ERROR_LABELS: Record<string, string> = {
  missing_token: "Λείπει GitHub Token. Πρόσθεσέ το στη «Ρύθμιση Token».",
  invalid_credentials: "Το GitHub Token είναι άκυρο ή έχει λήξει.",
  invalid_token_format: "Το token δεν έχει έγκυρη μορφή (χωρίς κενά, έως 512 χαρακτήρες).",
  invalid_app_name: "Μη έγκυρο όνομα εφαρμογής.",
  path_outside_apps_directory: "Μη έγκυρο όνομα εφαρμογής.",
  app_not_found: "Η εφαρμογή δεν βρέθηκε στις εφαρμογές του NOUS.",
  empty_app: "Δεν βρέθηκαν αρχεία προς δημοσίευση.",
  commit_failed: "Κάποια αρχεία δεν ανέβηκαν στο GitHub.",
  pages_enable_failed: "Τα αρχεία ανέβηκαν, αλλά το GitHub Pages δεν ενεργοποιήθηκε.",
  create_repo_failed: "Το GitHub δεν επέτρεψε τη δημιουργία repository.",
  network_error: "Αποτυχία σύνδεσης με το GitHub.",
};

/** Human-readable, secret-free error text for GitHub operator results. */
export function describeGithubError(error?: string | null, message?: string | null): string {
  const label = error ? GITHUB_ERROR_LABELS[error] : undefined;
  const text = label ?? message ?? error ?? "Άγνωστο σφάλμα";
  return String(redactForAudit(text)).replace(/\bgh[pousr]_[A-Za-z0-9_]{16,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b/g, "[REDACTED]");
}

export type GithubDeployPreview = {
  ok: boolean;
  dry_run?: boolean;
  token_configured?: boolean;
  ready?: boolean;
  repo_name?: string;
  owner?: string;
  pages_url?: string;
  files?: string[];
  total_bytes?: number;
  excluded_files?: { path: string; reason: string }[];
  error?: string;
  message?: string;
};

export type GithubRepo = {
  id: number;
  name: string;
  full_name: string;
  owner: string;
  html_url: string;
  description: string;
  default_branch: string;
  visibility: "public" | "private";
  updated_at: string;
  has_pages: boolean;
  pages_url: string | null;
  language: string | null;
  stars: number;
  open_issues: number;
  archived: boolean;
};

export type GithubTreeItem = {
  name: string;
  path: string;
  type: "file" | "dir";
  size: number;
  sha: string;
  html_url: string;
};

export type GithubFile = {
  name: string;
  path: string;
  sha: string;
  size: number;
  content: string;
  html_url: string;
};

export type GithubDeployResult = {
  ok: boolean;
  repo_name?: string;
  owner?: string;
  repo_url?: string;
  pages_enabled?: boolean;
  pages_url?: string;
  committed_files?: string[];
  failed_files?: { path: string; error: string }[];
  excluded_files?: { path: string; reason: string }[];
  partial?: boolean;
  pages_error?: string | null;
  error?: string;
  message?: string;
};

export async function fetchGithubStatus(): Promise<GithubStatus> {
  return await nousFetch<GithubStatus>("/remote/github/status");
}

export async function saveGithubConfig(
  token: string,
  defaultOwner?: string,
): Promise<{ ok: boolean; has_token: boolean; default_owner?: string }> {
  return await nousFetch("/remote/github/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, default_owner: defaultOwner }),
  });
}

export async function fetchGithubRepos(
  sort = "updated",
  perPage = 60,
): Promise<{ ok: boolean; count: number; repositories: GithubRepo[] }> {
  return await nousFetch(`/remote/github/repos?sort=${sort}&per_page=${perPage}`);
}

export async function fetchGithubTree(
  owner: string,
  repo: string,
  path = "",
  branch?: string,
): Promise<{ ok: boolean; items: GithubTreeItem[]; path: string; is_file?: boolean }> {
  const branchParam = branch ? `&branch=${encodeURIComponent(branch)}` : "";
  return await nousFetch(
    `/remote/github/tree?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}&path=${encodeURIComponent(path)}${branchParam}`,
  );
}

export async function fetchGithubFile(
  owner: string,
  repo: string,
  path: string,
  branch?: string,
): Promise<{
  ok: boolean;
  name?: string;
  path?: string;
  sha?: string;
  size?: number;
  content?: string;
}> {
  const branchParam = branch ? `&branch=${encodeURIComponent(branch)}` : "";
  return await nousFetch(
    `/remote/github/file?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}&path=${encodeURIComponent(path)}${branchParam}`,
  );
}

export async function commitGithubFile(params: {
  owner: string;
  repo: string;
  path: string;
  content: string;
  message: string;
  branch?: string;
  sha?: string;
}): Promise<{ ok: boolean; commit_sha?: string; commit_url?: string; error?: string }> {
  return await nousFetch("/remote/github/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

export async function deploySandboxAppToPages(params: {
  app_name: string;
  repo_name?: string;
  description?: string;
}): Promise<GithubDeployResult> {
  return await nousFetch("/remote/github/deploy-sandbox-app", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

export async function previewSandboxAppDeploy(params: {
  app_name: string;
  repo_name?: string;
}): Promise<GithubDeployPreview> {
  return await nousFetch("/remote/github/deploy-sandbox-app", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...params, dry_run: true }),
  });
}
