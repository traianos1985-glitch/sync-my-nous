import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, CircleAlert, Clock3, RefreshCw, ShieldCheck } from "lucide-react";

type Receipt = {
  id: string;
  operation: string;
  status: "queued" | "awaiting_approval" | "completed" | "failed" | string;
  verified: boolean;
  startedAt: string;
  completedAt: string | null;
  createdAt: string;
  evidence?: {
    provider?: string;
    model?: string;
    researchUsed?: boolean;
    persisted?: boolean;
  } | null;
  verification?: Record<string, unknown> | null;
};

type Filter = "all" | "pending" | "completed" | "failed" | "verified";

const statusLabels: Record<string, string> = {
  queued: "Σε αναμονή",
  awaiting_approval: "Αναμένει έγκριση",
  completed: "Ολοκληρώθηκε",
  failed: "Απέτυχε",
};

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("el-GR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function statusClass(status: string) {
  if (status === "completed") return "border-ok/30 bg-ok/10 text-ok";
  if (status === "failed") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  if (status === "awaiting_approval") {
    return "border-warn/30 bg-warn/10 text-warn";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

export function ExecutionReceiptsPanel() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await fetch("/api/receipts?limit=100", {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal,
      });
      const body = (await response.json().catch(() => null)) as {
        receipts?: Receipt[];
        error?: string;
      } | null;
      if (!response.ok) {
        const message =
          response.status === 401
            ? "Απαιτείται ενεργή σύνδεση χρήστη για την προβολή του ιστορικού."
            : (body?.error ?? `Αποτυχία φόρτωσης (HTTP ${response.status}).`);
        throw new Error(message);
      }
      setReceipts(Array.isArray(body?.receipts) ? body.receipts : []);
      setUpdatedAt(new Date().toISOString());
    } catch (cause) {
      if (cause instanceof Error && cause.name === "AbortError") return;
      setError(cause instanceof Error ? cause.message : "Δεν ήταν δυνατή η φόρτωση.");
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const filtered = useMemo(
    () =>
      receipts.filter((receipt) => {
        if (filter === "pending") {
          return receipt.status === "queued" || receipt.status === "awaiting_approval";
        }
        if (filter === "completed") return receipt.status === "completed";
        if (filter === "failed") return receipt.status === "failed";
        if (filter === "verified") return receipt.verified;
        return true;
      }),
    [filter, receipts],
  );

  const counts = useMemo(
    () => ({
      all: receipts.length,
      pending: receipts.filter(
        (item) => item.status === "queued" || item.status === "awaiting_approval",
      ).length,
      completed: receipts.filter((item) => item.status === "completed").length,
      failed: receipts.filter((item) => item.status === "failed").length,
      verified: receipts.filter((item) => item.verified).length,
    }),
    [receipts],
  );

  const filters: Array<{ id: Filter; label: string }> = [
    { id: "all", label: "Όλα" },
    { id: "pending", label: "Σε αναμονή" },
    { id: "completed", label: "Ολοκληρωμένα" },
    { id: "failed", label: "Αποτυχημένα" },
    { id: "verified", label: "Επαληθευμένα" },
  ];

  return (
    <div className="mt-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">
            Αποδεικτικά εκτέλεσης από το NOUS. Η καταχώριση δεν σημαίνει από μόνη της ότι μια
            ενέργεια επαληθεύτηκε.
          </p>
          {updatedAt && (
            <p className="mt-1 text-[11px] text-muted-foreground">
              Τελευταία ενημέρωση: {formatDate(updatedAt)}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => {
            setLoading(true);
            setError(null);
            void load();
          }}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-medium hover:border-primary disabled:opacity-50"
        >
          <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
          Ανανέωση
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {filters.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setFilter(item.id)}
            className={`rounded-xl border px-3 py-2 text-left text-xs transition-colors ${
              filter === item.id
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-card hover:border-primary/50"
            }`}
          >
            <span className="block text-muted-foreground">{item.label}</span>
            <strong className="mt-1 block font-mono text-lg">{counts[item.id]}</strong>
          </button>
        ))}
      </div>

      {error && (
        <div role="alert" className="rounded-xl border border-warn/40 bg-warn/5 p-4 text-sm">
          <div className="flex items-center gap-2 font-semibold text-warn">
            <CircleAlert className="size-4" /> Δεν φορτώθηκε το ιστορικό
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{error}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            Αν μόλις ενεργοποιήθηκε το νέο σύστημα receipts, επιβεβαίωσε ότι εφαρμόστηκε η SQL
            migration στη σωστή PostgreSQL βάση.
          </p>
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              setError(null);
              void load();
            }}
            className="mt-3 rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
          >
            Προσπάθεια ξανά
          </button>
        </div>
      )}

      {loading && receipts.length === 0 ? (
        <p className="rounded-xl border border-border p-6 text-center text-sm text-muted-foreground">
          Φόρτωση ιστορικού εκτελέσεων…
        </p>
      ) : filtered.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
          {receipts.length === 0
            ? "Δεν υπάρχουν ακόμη καταχωρισμένες εκτελέσεις."
            : "Δεν υπάρχουν εγγραφές σε αυτή την κατηγορία."}
        </p>
      ) : (
        <div className="space-y-2">
          {filtered.map((receipt) => (
            <article key={receipt.id} className="rounded-xl border border-border bg-card/70 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold capitalize">{receipt.operation}</p>
                  <p className="mt-1 break-all font-mono text-[10px] text-muted-foreground">
                    {receipt.id}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full border px-2.5 py-1 text-[11px] font-medium ${statusClass(
                      receipt.status,
                    )}`}
                  >
                    {statusLabels[receipt.status] ?? receipt.status}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] ${
                      receipt.verified
                        ? "border-ok/30 bg-ok/10 text-ok"
                        : "border-border text-muted-foreground"
                    }`}
                  >
                    {receipt.verified ? (
                      <ShieldCheck className="size-3" />
                    ) : (
                      <Clock3 className="size-3" />
                    )}
                    {receipt.verified ? "Επαληθευμένο" : "Μη επαληθευμένο"}
                  </span>
                </div>
              </div>
              <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                <p>
                  <span className="text-muted-foreground">Έναρξη:</span>{" "}
                  {formatDate(receipt.startedAt)}
                </p>
                <p>
                  <span className="text-muted-foreground">Ολοκλήρωση:</span>{" "}
                  {formatDate(receipt.completedAt)}
                </p>
                {receipt.evidence?.provider && (
                  <p>
                    <span className="text-muted-foreground">Provider:</span>{" "}
                    {receipt.evidence.provider}
                  </p>
                )}
                {receipt.evidence?.model && (
                  <p>
                    <span className="text-muted-foreground">Model:</span> {receipt.evidence.model}
                  </p>
                )}
                {typeof receipt.evidence?.researchUsed === "boolean" && (
                  <p>
                    <span className="text-muted-foreground">Research:</span>{" "}
                    {receipt.evidence.researchUsed ? "Ναι" : "Όχι"}
                  </p>
                )}
                {typeof receipt.evidence?.persisted === "boolean" && (
                  <p>
                    <span className="text-muted-foreground">Persisted:</span>{" "}
                    {receipt.evidence.persisted ? "Ναι" : "Όχι"}
                  </p>
                )}
              </div>
              {receipt.verified && (
                <p className="mt-3 flex items-center gap-1 text-[11px] text-ok">
                  <CheckCircle2 className="size-3" /> Υπάρχει αποτέλεσμα επαλήθευσης.
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
