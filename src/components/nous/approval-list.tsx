import { useState } from "react";
import { Check, ChevronDown, ChevronUp, Copy, Loader2, RotateCcw, Terminal } from "lucide-react";

import { formatApprovalPayload, type PendingApproval } from "./approval-model";
export type { PendingApproval };

export function ApprovalList({
  approvals,
  status,
  onResolve,
  onRefresh,
}: {
  approvals: PendingApproval[];
  status: "idle" | "loading" | "error";
  onResolve: (id: string, decision: "approved" | "rejected") => Promise<void>;
  onRefresh?: () => void;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const copyPayload = async (id: string, payload: string) => {
    try {
      await navigator.clipboard.writeText(payload);
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // ignore clipboard failures
    }
  };

  const resolve = async (id: string, decision: "approved" | "rejected") => {
    setBusyId(id);
    try {
      await onResolve(id, decision);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground">Ουρά εγκρίσεων</span>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
              approvals.length > 0 ? "bg-warn/15 text-warn" : "bg-muted text-muted-foreground"
            }`}
          >
            {approvals.length === 1
              ? "1 σε εκκρεμότητα"
              : approvals.length > 1
                ? `${approvals.length} σε εκκρεμότητα`
                : "Καμία εκκρεμότητα"}
          </span>
        </div>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={status === "loading"}
            className="flex items-center gap-1 rounded-md border border-border px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground disabled:opacity-50"
            title="Ανανέωση ουράς εγκρίσεων"
          >
            {status === "loading" ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <RotateCcw className="size-3" />
            )}
            Ανανέωση
          </button>
        )}
      </div>

      {status === "error" && (
        <p className="mb-2 text-xs text-destructive">Η approval queue δεν είναι διαθέσιμη.</p>
      )}
      {status === "loading" && approvals.length === 0 && (
        <p className="text-xs text-muted-foreground">Φόρτωση εγκρίσεων…</p>
      )}
      {status === "idle" && approvals.length === 0 && (
        <p className="text-xs text-muted-foreground">Δεν υπάρχουν pending approvals.</p>
      )}

      <div className="space-y-2.5">
        {approvals.map((approval) => {
          const busy = busyId === approval.id;
          const isExpanded = Boolean(expandedIds[approval.id]);
          const payload = formatApprovalPayload(approval.input);
          const hasPayload = payload !== "—" && payload !== "{}" && payload !== '""';

          return (
            <div
              key={approval.id}
              className="flex flex-col gap-2 rounded-xl border border-border/70 bg-card/70 p-3"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-primary uppercase">
                      Εργαλείο
                    </span>
                    <p className="truncate font-mono text-xs font-semibold text-foreground">
                      {approval.tool}
                    </p>
                  </div>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Ζητήθηκε {new Date(approval.createdAt).toLocaleString("el-GR")}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {hasPayload && (
                    <button
                      type="button"
                      onClick={() => toggleExpand(approval.id)}
                      className="flex items-center gap-1 rounded-md border border-border/80 px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
                    >
                      <Terminal className="size-3" />
                      <span>Παράμετροι</span>
                      {isExpanded ? (
                        <ChevronUp className="size-3" />
                      ) : (
                        <ChevronDown className="size-3" />
                      )}
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void resolve(approval.id, "approved")}
                    className="flex items-center gap-1 rounded-md bg-ok/15 px-3 py-1.5 text-xs font-semibold text-ok hover:bg-ok/25 disabled:opacity-50"
                  >
                    {busy && <Loader2 className="size-3 animate-spin" />}
                    {busy ? "Εκτέλεση…" : "Έγκριση"}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void resolve(approval.id, "rejected")}
                    className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
                  >
                    Απόρριψη
                  </button>
                </div>
              </div>

              {isExpanded && hasPayload && (
                <div className="mt-2 rounded-lg border border-border bg-background/90 p-2.5">
                  <div className="mb-1.5 flex items-center justify-between text-[10px] text-muted-foreground">
                    <span className="uppercase tracking-wider font-semibold">
                      Παράμετροι κλήσης (payload)
                    </span>
                    <button
                      type="button"
                      onClick={() => void copyPayload(approval.id, payload)}
                      className="flex items-center gap-1 rounded px-1.5 py-0.5 hover:bg-muted hover:text-foreground"
                    >
                      {copiedId === approval.id ? (
                        <>
                          <Check className="size-3 text-ok" />
                          <span className="text-ok">Αντιγράφηκε</span>
                        </>
                      ) : (
                        <>
                          <Copy className="size-3" />
                          <span>Αντιγραφή</span>
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded border border-border/50 bg-card/60 p-2 font-mono text-[11px] leading-relaxed text-foreground">
                    {payload}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
