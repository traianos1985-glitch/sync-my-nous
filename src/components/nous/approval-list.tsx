import { useState } from "react";

export type PendingApproval = { id: string; tool: string; input: unknown; createdAt: string };

export function ApprovalList({
  approvals,
  status,
  onResolve,
}: {
  approvals: PendingApproval[];
  status: "idle" | "loading" | "error";
  onResolve: (id: string, decision: "approved" | "rejected") => Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);

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
      {status === "error" && (
        <p className="mb-2 text-xs text-destructive">Η approval queue δεν είναι διαθέσιμη.</p>
      )}
      {status === "loading" && approvals.length === 0 && (
        <p className="text-xs text-muted-foreground">Φόρτωση εγκρίσεων…</p>
      )}
      {status === "idle" && approvals.length === 0 && (
        <p className="text-xs text-muted-foreground">Δεν υπάρχουν pending approvals.</p>
      )}
      <div className="space-y-2">
        {approvals.map((approval) => {
          const busy = busyId === approval.id;
          return (
            <div
              key={approval.id}
              className="flex flex-col gap-3 rounded-xl border border-border/70 bg-card/70 p-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate font-mono text-xs text-foreground">{approval.tool}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Ζητήθηκε {new Date(approval.createdAt).toLocaleString("el-GR")}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void resolve(approval.id, "approved")}
                  className="rounded-md bg-ok/15 px-3 py-1.5 text-xs font-semibold text-ok disabled:opacity-50"
                >
                  {busy ? "…" : "Έγκριση"}
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void resolve(approval.id, "rejected")}
                  className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground disabled:opacity-50"
                >
                  Απόρριψη
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
