import { useEffect, useState, useMemo } from "react";
import {
  ExternalLink,
  FolderGit2,
  Globe,
  Loader2,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Folder,
  ArrowLeft,
  Save,
  KeyRound,
  Sparkles,
  Rocket,
  Code2,
  Eye,
  GitBranch,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "./dashboard-primitives";
import {
  fetchGithubStatus,
  fetchGithubRepos,
  fetchGithubTree,
  fetchGithubFile,
  commitGithubFile,
  deploySandboxAppToPages,
  previewSandboxAppDeploy,
  saveGithubConfig,
  githubTokenState,
  canWriteToGithub,
  describeGithubError,
  type GithubDeployPreview,
  type GithubStatus,
  type GithubRepo,
  type GithubTreeItem,
  type GithubFile,
} from "./github-operator-model";

interface GithubOperatorStudioProps {
  connected: boolean;
}

export function GithubOperatorStudio({ connected }: GithubOperatorStudioProps) {
  // Global status
  const [status, setStatus] = useState<GithubStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  // Token configuration state
  const [showConfig, setShowConfig] = useState(false);
  const [patInput, setPatInput] = useState("");
  const [ownerInput, setOwnerInput] = useState("");
  const [savingConfig, setSavingConfig] = useState(false);
  const [configMessage, setConfigMessage] = useState<string | null>(null);

  // Tabs: "repos" | "editor" | "deploy"
  const [activeTab, setActiveTab] = useState<"repos" | "editor" | "deploy">("repos");

  // Repositories state
  const [repos, setRepos] = useState<GithubRepo[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [repoFilter, setRepoFilter] = useState<"all" | "pages">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Editor state (inspecting a repo)
  const [selectedRepo, setSelectedRepo] = useState<GithubRepo | null>(null);
  const [currentPath, setCurrentPath] = useState<string>("");
  const [treeItems, setTreeItems] = useState<GithubTreeItem[]>([]);
  const [loadingTree, setLoadingTree] = useState(false);
  const [activeFile, setActiveFile] = useState<GithubFile | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const [fileContentDraft, setFileContentDraft] = useState<string>("");
  const [commitMessage, setCommitMessage] = useState<string>("");
  const [committing, setCommitting] = useState(false);
  const [commitStatus, setCommitStatus] = useState<{ success: boolean; message: string } | null>(
    null,
  );

  // Deploy state
  const [deployAppName, setDeployAppName] = useState("");
  const [deployRepoName, setDeployRepoName] = useState("");
  const [deployDescription, setDeployDescription] = useState("");
  const [deploying, setDeploying] = useState(false);
  const [deployResult, setDeployResult] = useState<{
    success: boolean;
    repoUrl?: string;
    pagesUrl?: string;
    error?: string;
  } | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [deployPreview, setDeployPreview] = useState<GithubDeployPreview | null>(null);

  const tokenState = githubTokenState(status);
  const canWrite = canWriteToGithub(status);

  // Load status on mount
  useEffect(() => {
    if (connected) {
      loadStatus();
      loadRepos();
    }
  }, [connected]);

  async function loadStatus() {
    setLoadingStatus(true);
    try {
      const res = await fetchGithubStatus();
      setStatus(res);
      if (res.login || res.default_owner) {
        setOwnerInput(res.login || res.default_owner || "");
      }
    } catch {
      setStatus({ ok: false, connected: false, error: "status_failed" });
    } finally {
      setLoadingStatus(false);
    }
  }

  async function loadRepos() {
    setLoadingRepos(true);
    try {
      const res = await fetchGithubRepos();
      if (res.ok && Array.isArray(res.repositories)) {
        setRepos(res.repositories);
      }
    } catch {
      setRepos([]);
    } finally {
      setLoadingRepos(false);
    }
  }

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    setSavingConfig(true);
    setConfigMessage(null);
    try {
      const res = await saveGithubConfig(patInput, ownerInput || undefined);
      if (res.ok) {
        setConfigMessage("✅ Το GitHub Token αποθηκεύτηκε επιτυχώς!");
        setPatInput("");
        await loadStatus();
        await loadRepos();
      } else {
        setConfigMessage(`❌ ${describeGithubError((res as { error?: string }).error)}`);
      }
    } catch (err: unknown) {
      setPatInput("");
      setConfigMessage(
        `❌ Σφάλμα: ${describeGithubError(null, err instanceof Error ? err.message : null)}`,
      );
    } finally {
      setSavingConfig(false);
    }
  }

  async function openRepoTree(repo: GithubRepo, path = "") {
    setSelectedRepo(repo);
    setCurrentPath(path);
    setActiveFile(null);
    setCommitStatus(null);
    setActiveTab("editor");
    setLoadingTree(true);
    try {
      const res = await fetchGithubTree(repo.owner, repo.name, path, repo.default_branch);
      if (res.ok && Array.isArray(res.items)) {
        setTreeItems(res.items);
      }
    } catch {
      setTreeItems([]);
    } finally {
      setLoadingTree(false);
    }
  }

  async function openFile(item: GithubTreeItem) {
    if (!selectedRepo) return;
    setLoadingFile(true);
    setCommitStatus(null);
    try {
      const res = await fetchGithubFile(
        selectedRepo.owner,
        selectedRepo.name,
        item.path,
        selectedRepo.default_branch,
      );
      if (res.ok && res.content !== undefined) {
        const fileObj: GithubFile = {
          name: res.name || item.name,
          path: res.path || item.path,
          sha: res.sha || item.sha,
          size: res.size || item.size,
          content: res.content,
          html_url: item.html_url,
        };
        setActiveFile(fileObj);
        setFileContentDraft(res.content);
        setCommitMessage(`update: ${item.name} via NOUS AI OS`);
      }
    } catch (err: unknown) {
      alert(
        `Αποτυχία ανάγνωσης αρχείου: ${describeGithubError(null, err instanceof Error ? err.message : null)}`,
      );
    } finally {
      setLoadingFile(false);
    }
  }

  async function handleCommit() {
    if (!selectedRepo || !activeFile) return;
    setCommitting(true);
    setCommitStatus(null);
    try {
      const res = await commitGithubFile({
        owner: selectedRepo.owner,
        repo: selectedRepo.name,
        path: activeFile.path,
        content: fileContentDraft,
        message: commitMessage || `update: ${activeFile.name} via NOUS AI OS`,
        branch: selectedRepo.default_branch,
        sha: activeFile.sha,
      });
      if (res.ok) {
        setCommitStatus({
          success: true,
          message: `Επιτυχές commit! SHA: ${res.commit_sha?.slice(0, 7)}`,
        });
        // Refresh file content sha
        const updated = await fetchGithubFile(
          selectedRepo.owner,
          selectedRepo.name,
          activeFile.path,
          selectedRepo.default_branch,
        );
        if (updated.ok && updated.sha) {
          setActiveFile((prev) => (prev ? { ...prev, sha: updated.sha! } : null));
        }
      } else {
        setCommitStatus({
          success: false,
          message: `Αποτυχία: ${describeGithubError(res.error, "Σφάλμα commit")}`,
        });
      }
    } catch (err: unknown) {
      setCommitStatus({
        success: false,
        message: describeGithubError(null, err instanceof Error ? err.message : "Σφάλμα commit"),
      });
    } finally {
      setCommitting(false);
    }
  }

  async function handleDeploySandboxApp(e: React.FormEvent) {
    e.preventDefault();
    if (!deployAppName.trim()) return;
    setDeploying(true);
    setDeployResult(null);
    try {
      const res = await deploySandboxAppToPages({
        app_name: deployAppName.trim(),
        repo_name: deployRepoName.trim() || undefined,
        description: deployDescription.trim() || undefined,
      });
      if (res.ok) {
        setDeployResult({
          success: true,
          repoUrl: res.repo_url,
          pagesUrl: res.pages_url,
        });
        await loadRepos();
      } else {
        const failed = res.failed_files?.length
          ? ` (${res.failed_files.map((f) => f.path).join(", ")})`
          : "";
        setDeployResult({
          success: false,
          error: describeGithubError(res.error, res.message) + failed,
        });
      }
    } catch (err: unknown) {
      setDeployResult({
        success: false,
        error: describeGithubError(null, err instanceof Error ? err.message : "Σφάλμα deployment"),
      });
    } finally {
      setDeploying(false);
    }
  }

  async function handlePreviewDeploy() {
    if (!deployAppName.trim()) return;
    setPreviewing(true);
    setDeployPreview(null);
    setDeployResult(null);
    try {
      const res = await previewSandboxAppDeploy({
        app_name: deployAppName.trim(),
        repo_name: deployRepoName.trim() || undefined,
      });
      setDeployPreview(res);
    } catch (err: unknown) {
      setDeployPreview({
        ok: false,
        error: describeGithubError(null, err instanceof Error ? err.message : null),
      });
    } finally {
      setPreviewing(false);
    }
  }

  const filteredRepos = useMemo(() => {
    return repos.filter((r) => {
      const matchesFilter = repoFilter === "all" || (repoFilter === "pages" && r.has_pages);
      const matchesQuery =
        searchQuery.trim() === "" ||
        r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.description && r.description.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesFilter && matchesQuery;
    });
  }, [repos, repoFilter, searchQuery]);

  return (
    <div className="flex flex-col gap-6 p-4 md:p-6 max-w-7xl mx-auto w-full">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <FolderGit2 className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">GitHub & Pages Operator</h1>
            <p className="text-xs text-muted-foreground">
              Διαχείριση repositories, έλεγχος & αναβάθμιση κώδικα και άμεσο deployment στο GitHub
              Pages.
            </p>
          </div>
        </div>

        {/* Status Pill & Setup Button */}
        <div className="flex items-center gap-2">
          {loadingStatus ? (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Έλεγχος...
            </span>
          ) : status?.connected ? (
            <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Συνδέθηκε: @{status.login}</span>
              {status.rate_limit_remaining !== undefined && (
                <span className="opacity-60 text-[10px]">
                  ({status.rate_limit_remaining} API reqs)
                </span>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>
                {tokenState === "invalid"
                  ? "Άκυρο Token"
                  : tokenState === "error"
                    ? "Σφάλμα σύνδεσης"
                    : "Απαιτείται Token"}
              </span>
            </div>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConfig(!showConfig)}
            className="text-xs gap-1.5"
          >
            <KeyRound className="h-3.5 w-3.5" />
            {showConfig ? "Κλείσιμο Ρυθμίσεων" : "Ρύθμιση Token"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              loadStatus();
              loadRepos();
            }}
            disabled={loadingRepos}
            className="text-xs gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loadingRepos ? "animate-spin" : ""}`} />
            Ανανέωση
          </Button>
        </div>
      </div>

      {!connected && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-xl border border-border bg-muted/30 p-3 text-xs text-muted-foreground"
        >
          <KeyRound className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            Βάλε πρώτα το NOUS token στις Ρυθμίσεις για να συνδεθεί αυτή η οθόνη με τον NOUS.
          </span>
        </div>
      )}

      {connected && (tokenState === "missing" || tokenState === "invalid") && (
        <div
          role="alert"
          data-testid="github-token-missing"
          className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200"
        >
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
            <div className="flex flex-col gap-1">
              <span className="font-semibold text-amber-300">
                {tokenState === "missing"
                  ? "Λείπει το GitHub Token"
                  : "Το GitHub Token δεν είναι έγκυρο"}
              </span>
              <span>
                Μπορείς να δεις μόνο δημόσια repositories. Οι αλλαγές κώδικα και η δημοσίευση στο
                GitHub Pages είναι απενεργοποιημένες μέχρι να προσθέσεις έγκυρο token.
              </span>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="text-xs"
            onClick={() => setShowConfig(true)}
          >
            <KeyRound className="h-3.5 w-3.5" /> Πρόσθεση Token
          </Button>
        </div>
      )}

      {/* Expandable Token Config Box */}
      {showConfig && (
        <Card title="Ρύθμιση GitHub Personal Access Token (PAT)">
          <form onSubmit={handleSaveConfig} className="flex flex-col gap-3 p-2">
            <p className="text-xs text-muted-foreground">
              Εισήγαγε ένα GitHub Personal Access Token (classic ή fine-grained) με scopes{" "}
              <code className="text-primary font-mono">repo</code> και{" "}
              <code className="text-primary font-mono">workflow</code> για να μπορεί ο NOUS να
              διαβάζει, να τροποποιεί και να δημοσιεύει εφαρμογές στα repos σου.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  GitHub Token (PAT)
                </label>
                <input
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="ghp_..."
                  value={patInput}
                  onChange={(e) => setPatInput(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs font-mono outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground mb-1 block">
                  Προεπιλεγμένος Λογαριασμός / Οργανισμός
                </label>
                <input
                  type="text"
                  placeholder="π.χ. traianos1985-glitch"
                  value={ownerInput}
                  onChange={(e) => setOwnerInput(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"
                />
              </div>
            </div>
            <div className="flex items-center justify-between pt-2">
              {configMessage && <span className="text-xs font-medium">{configMessage}</span>}
              <Button
                type="submit"
                size="sm"
                disabled={savingConfig || !patInput.trim()}
                className="ml-auto text-xs"
              >
                {savingConfig ? "Αποθήκευση..." : "Αποθήκευση & Σύνδεση"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex gap-2 border-b border-border/40 pb-2">
        <button
          onClick={() => setActiveTab("repos")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-lg transition-colors ${
            activeTab === "repos"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted/40"
          }`}
        >
          <FolderGit2 className="h-4 w-4" />
          Εφαρμογές & Repos ({repos.length})
        </button>
        <button
          onClick={() => setActiveTab("editor")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-lg transition-colors ${
            activeTab === "editor"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted/40"
          }`}
        >
          <Code2 className="h-4 w-4" />
          Επεξεργαστής & Επιθεώρηση {selectedRepo && `(${selectedRepo.name})`}
        </button>
        <button
          onClick={() => setActiveTab("deploy")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-lg transition-colors ${
            activeTab === "deploy"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted/40"
          }`}
        >
          <Rocket className="h-4 w-4" />
          Deploy στο GitHub Pages
        </button>
      </div>

      {/* Tab 1: Repositories & Pages Apps */}
      {activeTab === "repos" && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={repoFilter === "all" ? "default" : "outline"}
                onClick={() => setRepoFilter("all")}
                className="text-xs"
              >
                Όλα τα Repos
              </Button>
              <Button
                size="sm"
                variant={repoFilter === "pages" ? "default" : "outline"}
                onClick={() => setRepoFilter("pages")}
                className="text-xs gap-1.5"
              >
                <Globe className="h-3.5 w-3.5" />
                GitHub Pages Apps Μόνο
              </Button>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Αναζήτηση repo..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-1.5 text-xs outline-none focus:border-primary"
              />
            </div>
          </div>

          {loadingRepos ? (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mb-2" />
              <span className="text-xs">Φόρτωση repositories από GitHub...</span>
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border/80 p-8 text-center text-muted-foreground text-xs">
              Δεν βρέθηκαν repositories. Βεβαιώσου ότι έχεις ορίσει ένα έγκυρο GitHub Token.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredRepos.map((r) => (
                <div
                  key={r.id}
                  className="flex flex-col justify-between rounded-xl border border-border/60 bg-card p-4 transition-all hover:border-primary/50"
                >
                  <div className="flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-sm truncate hover:text-primary">
                        <a
                          href={r.html_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1"
                        >
                          {r.name}
                          <ExternalLink className="h-3 w-3 opacity-50" />
                        </a>
                      </h3>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground shrink-0">
                        {r.visibility}
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground line-clamp-2 min-h-[32px]">
                      {r.description || "Χωρίς περιγραφή."}
                    </p>

                    <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-muted-foreground">
                      {r.language && (
                        <span className="flex items-center gap-1 font-mono">
                          <span className="h-2 w-2 rounded-full bg-primary/70" />
                          {r.language}
                        </span>
                      )}
                      <span className="opacity-60">· Branch: {r.default_branch}</span>
                    </div>
                  </div>

                  {/* Actions & Pages Status */}
                  <div className="mt-4 pt-3 border-t border-border/40 flex flex-col gap-2">
                    {r.has_pages ? (
                      <div className="flex items-center justify-between bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-2.5 py-1.5 text-xs text-emerald-400">
                        <span className="flex items-center gap-1.5 font-medium">
                          <Globe className="h-3.5 w-3.5" />
                          Live Pages
                        </span>
                        {r.pages_url && (
                          <a
                            href={r.pages_url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center gap-1 text-[11px] font-semibold underline hover:opacity-80"
                          >
                            Άνοιγμα <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ) : (
                      <div className="text-[11px] text-muted-foreground opacity-60">
                        Δεν έχει ενεργό GitHub Pages
                      </div>
                    )}

                    <div className="flex gap-2 pt-1">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => openRepoTree(r)}
                        className="w-full text-xs gap-1.5"
                      >
                        <Code2 className="h-3.5 w-3.5" />
                        Επιθεώρηση & Αλλαγή Κώδικα
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Code Inspector & In-Browser Editor */}
      {activeTab === "editor" && (
        <div className="flex flex-col gap-4">
          {!selectedRepo ? (
            <div className="rounded-xl border border-dashed border-border/80 p-8 text-center text-muted-foreground text-xs">
              Επίλεξε πρώτα ένα repository από την καρτέλα «Εφαρμογές & Repos» για να εξετάσεις τα
              αρχεία του.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {/* Repo Breadcrumbs & Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 bg-muted/20 border border-border/60 rounded-xl p-3">
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (currentPath) {
                        const parts = currentPath.split("/").filter(Boolean);
                        parts.pop();
                        openRepoTree(selectedRepo, parts.join("/"));
                      } else {
                        setActiveTab("repos");
                      }
                    }}
                    className="h-8 px-2 text-xs gap-1"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    {currentPath ? "Πίσω" : "Πίσω στα Repos"}
                  </Button>

                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <GitBranch className="h-3.5 w-3.5 text-primary" />
                    <span className="font-semibold">
                      {selectedRepo.owner}/{selectedRepo.name}
                    </span>
                    <span className="text-muted-foreground">/</span>
                    <span className="text-primary">{currentPath || "(root)"}</span>
                  </div>
                </div>

                {selectedRepo.has_pages && selectedRepo.pages_url && (
                  <a
                    href={selectedRepo.pages_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium underline"
                  >
                    <Globe className="h-3.5 w-3.5" /> Live Site <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>

              {/* Layout: Left Tree, Right Editor */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                {/* File Tree (Col 4) */}
                <div className="lg:col-span-4 rounded-xl border border-border/60 bg-card p-3 flex flex-col gap-2 min-h-[400px]">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Δομή Αρχείων
                  </h4>
                  {loadingTree ? (
                    <div className="flex items-center justify-center p-8 text-muted-foreground text-xs">
                      <Loader2 className="h-4 w-4 animate-spin mr-2" /> Φόρτωση...
                    </div>
                  ) : treeItems.length === 0 ? (
                    <div className="text-xs text-muted-foreground p-4 text-center">
                      Δεν υπάρχουν αρχεία.
                    </div>
                  ) : (
                    <div className="flex flex-col gap-1 overflow-y-auto max-h-[500px]">
                      {treeItems.map((item) => (
                        <button
                          key={item.sha || item.name}
                          onClick={() => {
                            if (item.type === "dir") {
                              openRepoTree(selectedRepo, item.path);
                            } else {
                              openFile(item);
                            }
                          }}
                          className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors text-left ${
                            activeFile?.path === item.path
                              ? "bg-primary/20 text-primary font-medium"
                              : "hover:bg-muted/40 text-muted-foreground"
                          }`}
                        >
                          <span className="flex items-center gap-2 truncate">
                            {item.type === "dir" ? (
                              <Folder className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                            ) : (
                              <FileCode className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                            )}
                            <span className="truncate">{item.name}</span>
                          </span>
                          {item.type === "file" && (
                            <span className="text-[10px] opacity-40 shrink-0">
                              {(item.size / 1024).toFixed(1)} KB
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Editor / Viewer (Col 8) */}
                <div className="lg:col-span-8 rounded-xl border border-border/60 bg-card p-4 flex flex-col gap-3 min-h-[400px]">
                  {loadingFile ? (
                    <div className="flex flex-col items-center justify-center p-16 text-muted-foreground text-xs">
                      <Loader2 className="h-6 w-6 animate-spin mb-2" />
                      Ανάγνωση αρχείου από το GitHub...
                    </div>
                  ) : !activeFile ? (
                    <div className="flex flex-col items-center justify-center p-16 text-muted-foreground text-xs text-center">
                      <Eye className="h-8 w-8 mb-2 opacity-40" />
                      Επίλεξε ένα αρχείο από τη λίστα για προβολή ή τροποποίηση κώδικα.
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      {/* File Header Bar */}
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/40 pb-2">
                        <div className="flex items-center gap-2">
                          <FileCode className="h-4 w-4 text-primary" />
                          <span className="font-mono text-xs font-semibold">{activeFile.path}</span>
                          <span className="text-[10px] text-muted-foreground">
                            ({(activeFile.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <a
                          href={activeFile.html_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] text-muted-foreground hover:text-primary flex items-center gap-1"
                        >
                          Προβολή στο GitHub <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>

                      {/* Code Textarea */}
                      <textarea
                        value={fileContentDraft}
                        onChange={(e) => setFileContentDraft(e.target.value)}
                        rows={16}
                        className="w-full rounded-lg border border-border/80 bg-background/80 p-3 font-mono text-xs leading-relaxed outline-none focus:border-primary resize-y"
                      />

                      {/* Commit Section */}
                      <div className="flex flex-col sm:flex-row items-center gap-2 pt-2 border-t border-border/40">
                        <input
                          type="text"
                          placeholder="Μήνυμα commit (π.χ. fix: optimize page style)"
                          value={commitMessage}
                          onChange={(e) => setCommitMessage(e.target.value)}
                          className="w-full sm:flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary"
                        />
                        <Button
                          size="sm"
                          onClick={handleCommit}
                          disabled={committing || !commitMessage.trim() || !canWrite}
                          title={canWrite ? undefined : "Απαιτείται έγκυρο GitHub Token"}
                          className="w-full sm:w-auto text-xs gap-1.5 shrink-0"
                        >
                          {committing ? (
                            <>
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              Commit...
                            </>
                          ) : (
                            <>
                              <Save className="h-3.5 w-3.5" />
                              Commit & Push στο GitHub
                            </>
                          )}
                        </Button>
                      </div>

                      {commitStatus && (
                        <div
                          className={`p-2 rounded-lg text-xs font-medium flex items-center gap-2 ${
                            commitStatus.success
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-red-500/10 text-red-400 border border-red-500/20"
                          }`}
                        >
                          {commitStatus.success ? (
                            <CheckCircle2 className="h-4 w-4 shrink-0" />
                          ) : (
                            <AlertCircle className="h-4 w-4 shrink-0" />
                          )}
                          <span>{commitStatus.message}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Deploy Sandbox App to Pages */}
      {activeTab === "deploy" && (
        <Card title="Δημοσίευση Εφαρμογής NOUS στο GitHub Pages (1-Click Deploy)">
          <form onSubmit={handleDeploySandboxApp} className="flex flex-col gap-4 p-2 max-w-2xl">
            <p className="text-xs text-muted-foreground">
              Επίλεξε μια εφαρμογή που δημιούργησε ο NOUS στο App Studio ή στο Sandbox. Το σύστημα
              θα δημιουργήσει αυτόματα repository στο GitHub, θα ανεβάσει τον κώδικα και θα
              ενεργοποιήσει το GitHub Pages ώστε η εφαρμογή να είναι ζωντανή στο διαδίκτυο!
            </p>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-muted-foreground">
                Όνομα Εφαρμογής στο NOUS (φάκελος generated_apps)
              </label>
              <input
                type="text"
                placeholder="π.χ. field_larmor_calc"
                value={deployAppName}
                onChange={(e) => {
                  setDeployAppName(e.target.value);
                  if (!deployRepoName) setDeployRepoName(e.target.value);
                }}
                className="rounded-md border border-border bg-background px-3 py-2 text-xs font-mono outline-none focus:border-primary"
                required
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-muted-foreground">
                Όνομα νέου GitHub Repo (προαιρετικό)
              </label>
              <input
                type="text"
                placeholder="π.χ. field-larmor-calc"
                value={deployRepoName}
                onChange={(e) => setDeployRepoName(e.target.value)}
                className="rounded-md border border-border bg-background px-3 py-2 text-xs font-mono outline-none focus:border-primary"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-muted-foreground">
                Περιγραφή Εφαρμογής
              </label>
              <input
                type="text"
                placeholder="π.χ. Interactive Larmor calculator deployed via NOUS AI OS"
                value={deployDescription}
                onChange={(e) => setDeployDescription(e.target.value)}
                className="rounded-md border border-border bg-background px-3 py-2 text-xs outline-none focus:border-primary"
              />
            </div>

            <div className="mt-2 flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => void handlePreviewDeploy()}
                disabled={previewing || deploying || !deployAppName.trim() || !connected}
                className="text-xs gap-2"
              >
                {previewing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
                Δοκιμαστικός έλεγχος (χωρίς δημοσίευση)
              </Button>
              <Button
                type="submit"
                disabled={deploying || !deployAppName.trim() || !canWrite}
                title={canWrite ? undefined : "Απαιτείται έγκυρο GitHub Token"}
                className="text-xs gap-2"
              >
                {deploying ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Δημιουργία Repo & Deployment...
                  </>
                ) : (
                  <>
                    <Rocket className="h-4 w-4" />
                    🚀 Deploy στο GitHub Pages
                  </>
                )}
              </Button>
            </div>

            {!canWrite && connected && (
              <p className="text-[11px] text-amber-300">
                Η δημοσίευση απαιτεί GitHub Token. Ο δοκιμαστικός έλεγχος λειτουργεί και χωρίς αυτό.
              </p>
            )}

            {deployPreview && (
              <div
                data-testid="github-deploy-preview"
                className="rounded-xl border border-border/60 bg-muted/20 p-4 text-xs flex flex-col gap-2"
              >
                {deployPreview.ok ? (
                  <>
                    <div className="flex items-center gap-2 font-semibold">
                      {deployPreview.ready ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-amber-400" />
                      )}
                      {deployPreview.ready
                        ? "Έτοιμο για δημοσίευση"
                        : "Λείπει GitHub Token — δεν θα δημοσιευτεί τίποτα ακόμη"}
                    </div>
                    <p className="text-muted-foreground">
                      Repo:{" "}
                      <span className="font-mono">
                        {deployPreview.owner}/{deployPreview.repo_name}
                      </span>{" "}
                      · Διεύθυνση: <span className="font-mono">{deployPreview.pages_url}</span>
                    </p>
                    <p className="font-medium">
                      Θα ανέβουν {deployPreview.files?.length ?? 0} αρχεία (
                      {((deployPreview.total_bytes ?? 0) / 1024).toFixed(1)} KB):
                    </p>
                    <ul className="font-mono text-[11px] max-h-40 overflow-y-auto">
                      {deployPreview.files?.map((f) => (
                        <li key={f}>✓ {f}</li>
                      ))}
                    </ul>
                    {!!deployPreview.excluded_files?.length && (
                      <>
                        <p className="font-medium text-amber-300">
                          Εξαιρούνται για ασφάλεια {deployPreview.excluded_files.length} αρχεία:
                        </p>
                        <ul className="font-mono text-[11px] max-h-32 overflow-y-auto text-muted-foreground">
                          {deployPreview.excluded_files.map((f) => (
                            <li key={f.path}>
                              ✕ {f.path} <span className="opacity-60">({f.reason})</span>
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </>
                ) : (
                  <div className="flex items-center gap-2 text-red-400">
                    <AlertCircle className="h-4 w-4" />
                    {describeGithubError(deployPreview.error, deployPreview.message)}
                  </div>
                )}
              </div>
            )}

            {deployResult && (
              <div
                className={`p-4 rounded-xl text-xs flex flex-col gap-2 mt-2 ${
                  deployResult.success
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-red-500/10 text-red-400 border border-red-500/20"
                }`}
              >
                <div className="flex items-center gap-2 font-bold">
                  {deployResult.success ? (
                    <>
                      <CheckCircle2 className="h-4 w-4" />Η εφαρμογή δημοσιεύτηκε επιτυχώς!
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-4 w-4" />
                      Αποτυχία δημοσίευσης
                    </>
                  )}
                </div>

                {deployResult.success && (
                  <div className="flex flex-col gap-1 text-[11px] pt-1">
                    {deployResult.repoUrl && (
                      <p>
                        Repository:{" "}
                        <a
                          href={deployResult.repoUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="underline font-mono"
                        >
                          {deployResult.repoUrl}
                        </a>
                      </p>
                    )}
                    {deployResult.pagesUrl && (
                      <p className="font-semibold text-emerald-300">
                        Live GitHub Pages URL:{" "}
                        <a
                          href={deployResult.pagesUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="underline font-mono"
                        >
                          {deployResult.pagesUrl}
                        </a>
                      </p>
                    )}
                  </div>
                )}

                {deployResult.error && <p>{deployResult.error}</p>}
              </div>
            )}
          </form>
        </Card>
      )}
    </div>
  );
}
