import { nousFetch } from "@/lib/nous-api";

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
  message?: string;
  error?: string;
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
