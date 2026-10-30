export type SandboxAppFile = {
  name: string;
  size: number;
  size_kb?: number;
};

export type SandboxApp = {
  name: string;
  path: string;
  source: "persistent" | "legacy";
  file_count: number;
  files: SandboxAppFile[];
  run_command?: string;
};

export type SandboxProcessStatus = {
  ok: boolean;
  running: boolean;
  pid?: number;
  cmd?: string;
  log?: string;
  error?: string;
};

export type SandboxTestResult = {
  ok: boolean;
  status: string;
  duration_seconds?: number;
  stdout?: string;
  stderr?: string;
  error?: string;
};

export type MockRequestPreset = {
  name: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  description: string;
  body?: string;
};

export type MockEndpointResult = {
  status: number;
  statusText: string;
  durationMs: number;
  body: string;
  headers?: Record<string, string>;
  error?: string;
};

export type SandboxViewport = "responsive" | "desktop" | "tablet" | "mobile";

export const DEFAULT_MOCK_PRESETS: MockRequestPreset[] = [
  {
    name: "Health Check",
    method: "GET",
    path: "/",
    description: "Έλεγχος ρίζας εφαρμογής (HTML ή status ok)",
  },
  {
    name: "API Health",
    method: "GET",
    path: "/health",
    description: "Έλεγχος υγείας API backend",
  },
  {
    name: "Metrics / Status",
    method: "GET",
    path: "/status",
    description: "Ανάκτηση κατάστασης / μετρικών της εφαρμογής",
  },
  {
    name: "Echo Data Probe",
    method: "POST",
    path: "/echo",
    description: "Δοκιμαστική αποστολή δεδομένων JSON",
    body: JSON.stringify({ message: "Hello from NOUS Sandbox!", timestamp: 1700000000 }, null, 2),
  },
];

export function hasWebPreview(files: { name: string }[]): boolean {
  return files.some(
    (f) =>
      f.name.toLowerCase() === "index.html" ||
      f.name.toLowerCase().endsWith("/index.html") ||
      f.name.toLowerCase().endsWith(".html"),
  );
}

export function detectEntryFile(files: { name: string }[]): string {
  const priorities = [
    "index.html",
    "main.py",
    "app.py",
    "server.py",
    "run.py",
    "index.js",
    "main.js",
    "src/index.html",
  ];
  for (const prio of priorities) {
    const match = files.find(
      (f) => f.name.toLowerCase() === prio || f.name.toLowerCase().endsWith(`/${prio}`),
    );
    if (match) return match.name;
  }
  return files[0]?.name ?? "none";
}

export function getViewportWidth(viewport: SandboxViewport): string {
  switch (viewport) {
    case "mobile":
      return "375px";
    case "tablet":
      return "768px";
    case "desktop":
      return "1200px";
    case "responsive":
    default:
      return "100%";
  }
}

const ERROR_REGEX = /error|exception|fail|traceback|critical|warning/i;

export function filterSandboxLogs(log: string, filter: "all" | "errors" | "info"): string[] {
  if (!log) return [];
  const lines = log.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (filter === "all") return lines;
  if (filter === "errors") {
    return lines.filter((l) => ERROR_REGEX.test(l));
  }
  return lines.filter((l) => !ERROR_REGEX.test(l));
}

export function formatSandboxDuration(seconds?: number): string {
  if (seconds === undefined || Number.isNaN(seconds)) return "—";
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
  return `${seconds.toFixed(2)}s`;
}
