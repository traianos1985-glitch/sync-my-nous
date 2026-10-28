import { Activity, Clock3, Gauge, Layers3 } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ResourcePoint } from "./telemetry-model";
import { buildMissionDistribution, calculateResourceTone, formatUptime } from "./telemetry-model";

type Props = {
  history: ResourcePoint[];
  cpu?: number;
  memory?: number;
  uptime?: number;
  checkedAt: string | null;
  missions: { active: number; awaiting: number; failed: number };
  missionCount: number | null;
  geminiState: "idle" | "testing" | "ok" | "error";
};

const toneClasses = {
  ok: "text-ok",
  warn: "text-warn",
  destructive: "text-destructive",
} as const;

function formatPercent(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)}%` : "—";
}

export function TelemetryPanel({
  history,
  cpu,
  memory,
  uptime,
  checkedAt,
  missions,
  missionCount,
  geminiState,
}: Props) {
  const distribution = buildMissionDistribution(missions);
  const modelLabel =
    geminiState === "ok"
      ? "Συνδεδεμένο"
      : geminiState === "error"
        ? "Σφάλμα"
        : geminiState === "testing"
          ? "Έλεγχος…"
          : "Δεν ελέγχθηκε";
  const modelTone = geminiState === "ok" ? "ok" : geminiState === "error" ? "destructive" : "warn";

  return (
    <section aria-labelledby="telemetry-title" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 id="telemetry-title" className="font-display font-semibold">
            Μετρικές συστήματος
          </h2>
          <p className="text-xs text-muted-foreground">
            Ιστορικό από τους τελευταίους ελέγχους, ανανέωση κάθε 60″
          </p>
        </div>
        {checkedAt && (
          <span className="text-[11px] text-muted-foreground">
            Ενημερώθηκε {new Date(checkedAt).toLocaleTimeString("el-GR")}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          {
            label: "CPU",
            value: formatPercent(cpu),
            tone: calculateResourceTone(cpu),
            icon: Gauge,
          },
          {
            label: "Μνήμη",
            value: formatPercent(memory),
            tone: calculateResourceTone(memory),
            icon: Activity,
          },
          { label: "Uptime", value: formatUptime(uptime), tone: "ok" as const, icon: Clock3 },
          {
            label: "Missions backend",
            value: missionCount ?? "—",
            tone: "ok" as const,
            icon: Layers3,
          },
        ].map(({ label, value, tone, icon: Icon }) => (
          <div key={label} className="rounded-xl border border-border bg-background/60 p-3">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
              <Icon className="size-3" />
              {label}
            </div>
            <p className={`mt-2 font-mono text-lg font-semibold ${toneClasses[tone]}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-background/40 p-3">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-xs font-semibold">CPU & Μνήμη</h3>
            <span className="text-[10px] text-muted-foreground">% · έως 12 σημεία</span>
          </div>
          {history.length < 2 ? (
            <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-border text-center text-xs text-muted-foreground">
              Συλλέγονται δεδομένα. Χρειάζονται τουλάχιστον δύο έλεγχοι για το γράφημα.
            </div>
          ) : (
            <div className="h-40" role="img" aria-label="Ιστορικό CPU και μνήμης">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history} margin={{ top: 5, right: 8, left: -24, bottom: 0 }}>
                  <defs>
                    <linearGradient id="cpuFill" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="var(--color-signal, #38bdf8)"
                        stopOpacity={0.3}
                      />
                      <stop offset="95%" stopColor="var(--color-signal, #38bdf8)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="memoryFill" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="var(--color-violet, #8b5cf6)"
                        stopOpacity={0.3}
                      />
                      <stop offset="95%" stopColor="var(--color-violet, #8b5cf6)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="time" tick={{ fontSize: 9 }} minTickGap={20} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 11,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="cpu"
                    name="CPU %"
                    stroke="var(--color-signal, #38bdf8)"
                    fill="url(#cpuFill)"
                    connectNulls
                  />
                  <Area
                    type="monotone"
                    dataKey="memory"
                    name="Μνήμη %"
                    stroke="var(--color-violet, #8b5cf6)"
                    fill="url(#memoryFill)"
                    connectNulls
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-border bg-background/40 p-3">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-xs font-semibold">Κατάσταση missions</h3>
            <span className={`text-[10px] ${toneClasses[modelTone]}`}>Gemini: {modelLabel}</span>
          </div>
          <div className="h-40" role="img" aria-label="Πλήθος missions ανά κατάσταση">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 9 }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    borderColor: "hsl(var(--border))",
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                />
                <Bar
                  dataKey="count"
                  name="Αποστολές"
                  radius={[5, 5, 0, 0]}
                  fill="var(--color-signal, #38bdf8)"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
}
