export type StudioFile = { name: string; size: number };
export type StudioApp = {
  name: string;
  files: StudioFile[];
  file_count: number;
  run_command?: string;
};
export type StudioBuild = {
  plan_id: string;
  app_name: string;
  title?: string;
  status: string;
  files?: { path: string; content: string }[];
};
export type ValidationResult = {
  ok: boolean;
  status: string;
  stdout?: string;
  stderr?: string;
  error?: string;
  duration_seconds?: number;
  return_code?: number;
};
export type RepairProposal = {
  repair_id: string;
  app_name: string;
  status: string;
  summary: string;
  root_causes?: unknown[];
  risks?: string[];
  validation_plan?: string[];
  changes?: { path: string; content: string }[];
};
export type RepairDetail = {
  ok: boolean;
  proposal: RepairProposal;
  review: { ready_for_human_review: boolean; blockers: string[]; warnings: string[] };
  changes: { path: string; before: string; content: string; diff: string }[];
};
export type FileNode = { name: string; path: string; children: FileNode[]; file?: StudioFile };

export function fileTree(files: StudioFile[]): FileNode[] {
  const roots: FileNode[] = [];
  for (const file of files) {
    const parts = file.name.split("/");
    if (parts.some((p) => !p || p === "." || p === "..") || file.name.includes("\\")) continue;
    let children = roots;
    parts.forEach((name, index) => {
      const path = parts.slice(0, index + 1).join("/");
      let node = children.find((item) => item.path === path);
      if (!node) {
        node = { name, path, children: [] };
        children.push(node);
      }
      if (index === parts.length - 1) node.file = file;
      children = node.children;
    });
  }
  return roots;
}

export function canApproveRepair(detail: RepairDetail | null): boolean {
  return (
    detail?.proposal.status === "pending_review" &&
    detail.review.ready_for_human_review === true &&
    detail.review.blockers.length === 0
  );
}
export function appendConsole(current: string, text: string): string {
  return (current + text).slice(-24_000);
}
