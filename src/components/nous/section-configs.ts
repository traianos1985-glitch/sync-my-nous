export type SectionAction = {
  label: string;
  path: string;
  body?: Record<string, unknown>;
  input?: { key: string; placeholder: string };
  confirm?: string;
};

export type SectionConfig = {
  endpoints: Array<{ label: string; path: string }>;
  actions?: SectionAction[];
};

export const sectionConfigs: Record<string, SectionConfig> = {
  goals: {
    endpoints: [{ label: "Goals", path: "/remote/goals-v2/status" }],
    actions: [
      { label: "Δημιουργία βασικών goals", path: "/remote/goals-v2/seed" },
      { label: "Δημιουργία projects", path: "/remote/goal-manager-v2/generate" },
    ],
  },
  missions: {
    endpoints: [{ label: "Missions", path: "/remote/missions/status" }],
    actions: [
      {
        label: "Νέο system check mission",
        path: "/remote/missions/create-standard",
        body: { kind: "system_check" },
      },
      { label: "Εκτέλεση επόμενου βήματος", path: "/remote/missions/run-next" },
    ],
  },
  planner: {
    endpoints: [
      { label: "Planner", path: "/remote/mission-planner/status" },
      { label: "Proposals", path: "/remote/mission-planner/proposals" },
    ],
    actions: [{ label: "Πρότεινε mission", path: "/remote/mission-planner/propose" }],
  },
  brain: {
    endpoints: [
      { label: "Brain", path: "/remote/brain/status" },
      { label: "Knowledge", path: "/remote/knowledge/status" },
    ],
    actions: [{ label: "Αποθήκευση brain state", path: "/remote/brain/save" }],
  },
  appbuilder: {
    endpoints: [
      { label: "App Builder", path: "/remote/app-builder/status" },
      { label: "Builds", path: "/remote/app-builder/list" },
    ],
    actions: [
      {
        label: "Σχέδιο νέας εφαρμογής",
        path: "/remote/app-builder/plan",
        input: { key: "description", placeholder: "Περιέγραψε την εφαρμογή" },
      },
    ],
  },
  scheduler: {
    endpoints: [{ label: "Scheduler", path: "/remote/executive-scheduler-loop/status" }],
    actions: [
      { label: "Run once", path: "/remote/executive-scheduler-loop/run-once" },
      { label: "Start", path: "/remote/executive-scheduler-loop/start" },
      { label: "Stop", path: "/remote/executive-scheduler-loop/stop" },
    ],
  },
  deploy: {
    endpoints: [
      { label: "Deploy", path: "/remote/deploy/status" },
      { label: "Vercel", path: "/remote/vercel/status" },
      { label: "Providers", path: "/remote/deploy/providers" },
    ],
  },
  backup: {
    endpoints: [
      { label: "Backups", path: "/remote/brain-backup/list" },
      { label: "Restore", path: "/remote/brain-restore/status" },
    ],
    actions: [{ label: "Δημιουργία backup", path: "/remote/brain-backup/create" }],
  },
  larmor: {
    endpoints: [
      { label: "Larmor app", path: "/larmor/ping" },
      { label: "Ιστορικό", path: "/larmor/history" },
    ],
    actions: [
      {
        label: "Υπολογισμός (B σε Tesla)",
        path: "/larmor/calculate",
        body: { material: "cu" },
        input: { key: "b_field_T", placeholder: "π.χ. 0.04823" },
      },
    ],
  },
  field: {
    endpoints: [
      { label: "Markers", path: "/field/markers" },
      { label: "Ημερολόγιο", path: "/field/list?limit=10" },
    ],
  },
  "remote-access": {
    endpoints: [{ label: "Tunnel", path: "/remote/tunnel/status" }],
    actions: [
      {
        label: "Start tunnel",
        path: "/remote/tunnel/start",
        confirm: "Να ανοίξει δημόσιο tunnel προς τον NOUS;",
      },
      { label: "Stop tunnel", path: "/remote/tunnel/stop" },
    ],
  },
  autoexec: {
    endpoints: [{ label: "Auto Exec", path: "/remote/auto-mission-executor/status" }],
    actions: [
      { label: "Run", path: "/remote/auto-mission-executor/run" },
      { label: "Enable", path: "/remote/auto-mission-executor/enable" },
      { label: "Disable", path: "/remote/auto-mission-executor/disable" },
    ],
  },
  loopv3: {
    endpoints: [{ label: "Agent loop", path: "/remote/executive-loop-v3/status" }],
    actions: [
      {
        label: "Run cycle",
        path: "/remote/executive-loop-v3/run",
        body: { trigger: "dashboard" },
      },
    ],
  },
  autoscheduler: {
    endpoints: [{ label: "AutoSched", path: "/remote/auto-mission-scheduler/status" }],
    actions: [
      { label: "Run once", path: "/remote/auto-mission-scheduler/run-once" },
      { label: "Start", path: "/remote/auto-mission-scheduler/start" },
      { label: "Stop", path: "/remote/auto-mission-scheduler/stop" },
    ],
  },
  diagnosis: {
    endpoints: [{ label: "Diagnosis", path: "/remote/self-diagnosis/status" }],
    actions: [
      { label: "Εκτέλεση διάγνωσης", path: "/remote/self-diagnosis/run" },
      { label: "AI ανάλυση", path: "/remote/self-diagnosis/ai-analyze" },
    ],
  },
  repair: {
    endpoints: [
      { label: "Repair", path: "/remote/autonomous-repair/status" },
      { label: "Proposals", path: "/remote/autonomous-repair/proposals" },
    ],
    actions: [{ label: "Πρότεινε επισκευή", path: "/remote/autonomous-repair/propose" }],
  },
  selfheal: {
    endpoints: [
      { label: "Self heal", path: "/remote/self-healing/status" },
      { label: "Safety net", path: "/remote/safety/status" },
    ],
    actions: [
      { label: "Ανάλυση", path: "/remote/self-healing/run-analysis" },
      { label: "Reset circuit", path: "/remote/safety/circuit-reset" },
    ],
  },
  intelligence: {
    endpoints: [
      { label: "Intelligence", path: "/remote/executive-intelligence/status" },
      { label: "Report", path: "/remote/executive-intelligence/report" },
    ],
  },
  learning: {
    endpoints: [
      { label: "Learning", path: "/remote/learning/status" },
      { label: "Lessons", path: "/remote/lessons/status" },
    ],
    actions: [{ label: "Κύκλος μάθησης", path: "/remote/learning/run", body: { max_topics: 1 } }],
  },
  system: {
    endpoints: [
      { label: "Overview", path: "/api/system/overview" },
      { label: "Ops", path: "/remote/ops/status" },
      { label: "Reality", path: "/remote/reality/status" },
    ],
  },
  command: {
    endpoints: [{ label: "Command center", path: "/remote/command-center/status" }],
    actions: [
      {
        label: "Run cycle",
        path: "/remote/command-center/run-cycle",
        body: { trigger: "command_center" },
      },
    ],
  },
  approvals: {
    endpoints: [
      { label: "Tool approvals", path: "/api/approvals" },
      { label: "Mission approvals", path: "/remote/missions/approvals" },
      { label: "Operator approvals", path: "/remote/operator/approvals" },
    ],
  },
  audit: {
    endpoints: [
      { label: "Audit", path: "/api/audit?days=30" },
      { label: "Dashboard actions", path: "/remote/dashboard-action-audit" },
    ],
  },
  companion: {
    endpoints: [{ label: "Companion", path: "/remote/companion/status" }],
    actions: [
      { label: "Android Home", path: "/remote/companion/home" },
      { label: "Android Back", path: "/remote/companion/back" },
    ],
  },
  pending: {
    endpoints: [{ label: "Pending review", path: "/remote/pending-review/status" }],
  },
  graphs: {
    endpoints: [
      { label: "Knowledge graph", path: "/remote/knowledge-graph/status" },
      { label: "Repository graph", path: "/remote/repository-graph/status" },
    ],
    actions: [
      { label: "Build knowledge graph", path: "/remote/knowledge-graph/build" },
      { label: "Build repository graph", path: "/remote/repository-graph/build" },
    ],
  },
  analyst: {
    endpoints: [
      { label: "Code analyst", path: "/remote/code-analyst/status" },
      { label: "Reports", path: "/remote/code-analyst/reports" },
    ],
    actions: [
      {
        label: "Ανάλυση τελευταίας διάγνωσης",
        path: "/remote/code-analyst/analyze-latest-diagnosis",
      },
    ],
  },
  upgrades: {
    endpoints: [
      { label: "Upgrades", path: "/remote/upgrade-planner/status" },
      { label: "Plans", path: "/remote/upgrade-planner/plans" },
    ],
    actions: [{ label: "Πρότεινε upgrade", path: "/remote/upgrade-planner/propose" }],
  },
};
