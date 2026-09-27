import React, { useState } from "react";

export interface SwarmAgentStep {
  role: "architect" | "researcher" | "coder" | "reviewer";
  status: string;
  summary?: string;
  diff_summary?: string;
  verifications?: string[];
  findings?: string[];
  timestamp: number;
}

export interface SwarmVisualizerProps {
  mission?: string;
  steps?: SwarmAgentStep[];
  status?: "idle" | "running" | "completed" | "error";
  onRunMission?: (mission: string) => void;
}

const roleColors: Record<string, string> = {
  architect: "bg-purple-500/10 border-purple-500/30 text-purple-400",
  researcher: "bg-blue-500/10 border-blue-500/30 text-blue-400",
  coder: "bg-amber-500/10 border-amber-500/30 text-amber-400",
  reviewer: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
};

const roleIcons: Record<string, string> = {
  architect: "🏛️ Architect",
  researcher: "🔍 Researcher",
  coder: "💻 Coder",
  reviewer: "🛡️ Reviewer",
};

export const SwarmVisualizer: React.FC<SwarmVisualizerProps> = ({
  mission = "System Health & Maintenance Mission",
  steps = [],
  status = "completed",
  onRunMission,
}) => {
  const [inputMission, setInputMission] = useState("");

  return (
    <div className="rounded-xl border border-border bg-card p-5 text-card-foreground shadow-sm">
      <div className="flex items-center justify-between border-b border-border/40 pb-4">
        <div>
          <h3 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <span>⚡ Multi-Agent Swarm Orchestrator</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
              {status}
            </span>
          </h3>
          <p className="text-sm text-muted-foreground mt-0.5">
            Real-time delegation, execution tracing and automated self-healing.
          </p>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={inputMission}
          onChange={(e) => setInputMission(e.target.value)}
          placeholder="Enter custom mission for the swarm..."
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <button
          onClick={() => {
            if (inputMission && onRunMission) {
              onRunMission(inputMission);
              setInputMission("");
            }
          }}
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          Dispatch Swarm
        </button>
      </div>

      <div className="mt-6 space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Live Agent Swarm Pipeline
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {(["architect", "researcher", "coder", "reviewer"] as const).map((role) => {
            const agentStep = steps.find((s) => s.role === role);
            return (
              <div
                key={role}
                className={`rounded-lg border p-3 flex flex-col justify-between transition-all ${
                  roleColors[role]
                }`}
              >
                <div className="flex items-center justify-between font-medium text-sm">
                  <span>{roleIcons[role]}</span>
                  <span className="text-xs opacity-80 uppercase">
                    {agentStep ? agentStep.status : "Ready"}
                  </span>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">
                  {agentStep?.summary ||
                    agentStep?.diff_summary ||
                    (agentStep?.verifications
                      ? `${agentStep.verifications.length} verified`
                      : "Awaiting dispatch")}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SwarmVisualizer;
