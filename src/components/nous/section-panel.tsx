import { useCallback, useEffect, useState } from "react";
import { Loader2, RotateCcw } from "lucide-react";
import { nousFetch } from "@/lib/nous-api";
import { sectionConfigs, type SectionAction } from "@/components/nous/section-configs";

type LoadState = { status: "loading" | "ready" | "error"; data?: unknown; error?: string };

export function SectionPanel({ section }: { section: string }) {
  const config = sectionConfigs[section];
  const [results, setResults] = useState<Record<string, LoadState>>({});
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [running, setRunning] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<{
    label: string;
    ok: boolean;
    data: unknown;
  } | null>(null);

  const load = useCallback(async () => {
    if (!config) return;
    setResults(
      Object.fromEntries(
        config.endpoints.map((endpoint) => [endpoint.path, { status: "loading" }]),
      ),
    );
    await Promise.all(
      config.endpoints.map(async (endpoint) => {
        try {
          const data = await nousFetch<unknown>(endpoint.path);
          setResults((current) => ({ ...current, [endpoint.path]: { status: "ready", data } }));
        } catch (error) {
          setResults((current) => ({
            ...current,
            [endpoint.path]: {
              status: "error",
              error: error instanceof Error ? error.message : "Αποτυχία φόρτωσης",
            },
          }));
        }
      }),
    );
  }, [config]);

  useEffect(() => {
    setActionResult(null);
    setInputs({});
    void load();
  }, [load]);

  if (!config) return null;

  const runAction = async (action: SectionAction) => {
    const value = action.input ? (inputs[action.path] ?? "").trim() : "";
    if (action.input && !value) {
      setActionResult({
        label: action.label,
        ok: false,
        data: `Συμπλήρωσε: ${action.input.placeholder}`,
      });
      return;
    }
    if (action.confirm && !window.confirm(action.confirm)) return;
    setRunning(action.path);
    try {
      const body = {
        ...(action.body ?? {}),
        ...(action.input ? { [action.input.key]: value } : {}),
      };
      const data = await nousFetch<unknown>(action.path, {
        method: "POST",
        body: JSON.stringify(body),
        timeoutMs: 90_000,
      });
      const ok = !(isRecord(data) && data["ok"] === false);
      setActionResult({ label: action.label, ok, data });
      await load();
    } catch (error) {
      setActionResult({
        label: action.label,
        ok: false,
        data: error instanceof Error ? error.message : "Η ενέργεια απέτυχε",
      });
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="mt-4 space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => void load()}
          className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
        >
          <RotateCcw className="size-3" /> Ανανέωση
        </button>
        {config.actions?.map((action) => (
          <div key={action.path} className="flex items-center gap-1">
            {action.input && (
              <input
                value={inputs[action.path] ?? ""}
                onChange={(event) =>
                  setInputs((current) => ({ ...current, [action.path]: event.target.value }))
                }
                placeholder={action.input.placeholder}
                aria-label={action.input.placeholder}
                className="w-48 rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs outline-none focus:border-primary"
              />
            )}
            <button
              type="button"
              onClick={() => void runAction(action)}
              disabled={running !== null}
              className="inline-flex items-center gap-1 rounded-lg border border-primary/40 bg-primary/5 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/10 disabled:opacity-50"
            >
              {running === action.path && <Loader2 className="size-3 animate-spin" />}
              {action.label}
            </button>
          </div>
        ))}
      </div>
      {actionResult && (
        <div
          role="status"
          className={`rounded-xl border p-3 text-xs ${actionResult.ok ? "border-ok/30 bg-ok/5" : "border-rose-400/30 bg-rose-400/5"}`}
        >
          <p className={`font-semibold ${actionResult.ok ? "text-ok" : "text-rose-300"}`}>
            {actionResult.label}: {actionResult.ok ? "ολοκληρώθηκε" : "απέτυχε"}
          </p>
          <DataView data={actionResult.data} />
        </div>
      )}
      {config.endpoints.map((endpoint) => {
        const result = results[endpoint.path];
        return (
          <div key={endpoint.path} className="rounded-xl border border-border bg-background/40 p-3">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {endpoint.label}
            </p>
            {!result || result.status === "loading" ? (
              <p className="text-xs text-muted-foreground">Φόρτωση…</p>
            ) : result.status === "error" ? (
              <p className="text-xs text-rose-300">{result.error}</p>
            ) : (
              <DataView data={result.data} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatPrimitive(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "ναι" : "όχι";
  return String(value);
}

function DataView({ data }: { data: unknown }) {
  if (typeof data === "string") {
    return <p className="whitespace-pre-wrap text-xs text-foreground/90">{data}</p>;
  }
  if (Array.isArray(data)) {
    if (data.length === 0) return <p className="text-xs text-muted-foreground">Καμία εγγραφή.</p>;
    return (
      <details className="text-xs">
        <summary className="cursor-pointer text-muted-foreground">{data.length} εγγραφές</summary>
        <pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-background/70 p-2 text-[11px]">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    );
  }
  if (!isRecord(data)) return <p className="text-xs">{formatPrimitive(data)}</p>;
  const entries = Object.entries(data).filter(([key]) => key !== "time");
  if (entries.length === 0) return <p className="text-xs text-muted-foreground">Κενή απάντηση.</p>;
  return (
    <div className="divide-y divide-border/50">
      {entries.map(([key, value]) => (
        <div key={key} className="flex min-w-0 items-start justify-between gap-3 py-1.5 text-xs">
          <span className="shrink-0 text-muted-foreground">{key}</span>
          {typeof value === "object" && value !== null ? (
            <details className="min-w-0 text-right">
              <summary className="cursor-pointer text-foreground/80">
                {Array.isArray(value) ? `${value.length} εγγραφές` : "λεπτομέρειες"}
              </summary>
              <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-background/70 p-2 text-left text-[11px]">
                {JSON.stringify(value, null, 2)}
              </pre>
            </details>
          ) : (
            <span className="min-w-0 break-words text-right text-foreground/90">
              {formatPrimitive(value)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
