export type ResourcePoint = {
  time: string;
  cpu: number | null;
  memory: number | null;
};

export type MissionDistributionPoint = {
  name: string;
  count: number;
  fill: string;
};

export function formatUptime(seconds?: number): string {
  if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) return "—";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}ω ${minutes}λ`;
  return `${minutes}λ ${Math.floor(seconds % 60)}δ`;
}

export function calculateResourceTone(percent?: number): "ok" | "warn" | "destructive" {
  if (typeof percent !== "number" || isNaN(percent)) return "ok";
  if (percent >= 85) return "destructive";
  if (percent >= 70) return "warn";
  return "ok";
}

export function buildMissionDistribution(summary: {
  active: number;
  awaiting: number;
  failed: number;
}): MissionDistributionPoint[] {
  return [
    { name: "Ενεργές", count: Math.max(0, summary.active), fill: "var(--color-signal, #38bdf8)" },
    {
      name: "Προς έγκριση",
      count: Math.max(0, summary.awaiting),
      fill: "var(--color-warn, #f59e0b)",
    },
    {
      name: "Αποτυχίες",
      count: Math.max(0, summary.failed),
      fill: "var(--color-destructive, #ef4444)",
    },
  ];
}

export function appendResourcePoint(
  history: ResourcePoint[],
  point: ResourcePoint,
  maxPoints = 12,
): ResourcePoint[] {
  const next = [...history, point];
  if (next.length > maxPoints) {
    return next.slice(next.length - maxPoints);
  }
  return next;
}
