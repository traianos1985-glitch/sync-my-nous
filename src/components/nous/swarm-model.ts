export type SwarmPlanItem = { id: number; role: string; task: string };

export type SwarmTraceItem = {
  role: string;
  status: string;
  summary?: string;
  plan?: SwarmPlanItem[];
  simulated?: boolean;
  executed?: boolean;
  timestamp?: number;
};

export type SwarmResult = {
  mission: string;
  status: string;
  simulated?: boolean;
  executed?: boolean;
  notice?: string;
  agent_count?: number;
  trace: SwarmTraceItem[];
  duration_s?: number;
};

export type SwarmNode = {
  role: string;
  label: string;
  description: string;
  status: string;
  statusLabel: string;
  summary: string;
  task?: string;
  executed: boolean;
};

export type SwarmView = {
  leader: SwarmNode | null;
  workers: SwarmNode[];
  simulated: boolean;
  executedCount: number;
};

export const MAX_MISSION_LENGTH = 2000;

export const SWARM_ROLES: Record<string, { label: string; description: string }> = {
  architect: { label: "Architect", description: "Σχεδιασμός και ανάθεση εργασιών" },
  researcher: { label: "Researcher", description: "Συλλογή πληροφοριών και πλαισίου" },
  coder: { label: "Coder", description: "Σύνθεση κώδικα και διορθώσεων" },
  reviewer: { label: "Reviewer", description: "Έλεγχοι ποιότητας και tests" },
};

const STATUS_LABELS: Record<string, string> = {
  planned: "Σχέδιο έτοιμο",
  done: "Ολοκληρώθηκε (προσομοίωση)",
  not_run: "Δεν εκτελέστηκε",
  failed: "Αποτυχία",
  pending: "Σε αναμονή",
};

export function swarmStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

/** Returns an error message for an invalid mission, or null when it can be sent. */
export function validateMission(text: string): string | null {
  const trimmed = text.trim();
  if (!trimmed) return "Γράψε μια αποστολή για το swarm.";
  if (trimmed.length > MAX_MISSION_LENGTH)
    return `Η αποστολή ξεπερνά τους ${MAX_MISSION_LENGTH} χαρακτήρες.`;
  return null;
}

function toNode(item: SwarmTraceItem | undefined, role: string, task?: string): SwarmNode {
  const meta = SWARM_ROLES[role] ?? { label: role, description: "" };
  const status = item?.status ?? "pending";
  return {
    role,
    label: meta.label,
    description: meta.description,
    status,
    statusLabel: swarmStatusLabel(status),
    summary: item?.summary ?? "",
    task,
    // Only an explicit executed:true from the backend counts as real work.
    executed: item?.executed === true,
  };
}

/** Turns the backend trace into a leader → workers view. */
export function buildSwarmView(result: SwarmResult | null): SwarmView {
  if (!result || !Array.isArray(result.trace) || result.trace.length === 0) {
    return { leader: null, workers: [], simulated: false, executedCount: 0 };
  }
  const [first, ...rest] = result.trace;
  const leader = toNode(first, first.role);
  const plan = Array.isArray(first.plan) ? first.plan : [];
  const remaining = [...rest];
  const workers = plan.map((step) => {
    const index = remaining.findIndex((item) => item.role === step.role);
    const match = index >= 0 ? remaining.splice(index, 1)[0] : undefined;
    return toNode(match, step.role, step.task);
  });
  const nodes = [leader, ...workers];
  return {
    leader,
    workers,
    simulated: result.simulated !== false || result.trace.some((t) => t.simulated === true),
    executedCount: nodes.filter((n) => n.executed).length,
  };
}
