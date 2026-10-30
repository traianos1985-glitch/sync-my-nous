import { useCallback, useEffect, useState } from "react";
import { Check, CircleAlert, Loader2, RefreshCw, Smartphone, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { nousFetch } from "@/lib/nous-api";

type Approval = { id: string; tool: string; missionId?: string | null; expiresAt: string };
type CompanionStatus = { available: boolean; package: string; commands: string[] };

export function MobileBridgePanel() {
  const [status, setStatus] = useState<CompanionStatus | null>(null);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [companion, pending] = await Promise.all([
        nousFetch<CompanionStatus>("/remote/companion/status"),
        nousFetch<{ ok: boolean; approvals: Approval[] }>("/api/approvals"),
      ]);
      setStatus(companion);
      setApprovals(pending.approvals ?? []);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    queueMicrotask(refresh);
  }, [refresh]);

  async function resolveApproval(id: string, decision: "approved" | "rejected") {
    setBusy(id);
    try {
      await nousFetch("/api/approvals", {
        method: "PATCH",
        body: JSON.stringify({ id, status: decision }),
      });
      setApprovals((items) => items.filter((item) => item.id !== id));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section
      className="mt-4 overflow-hidden rounded-2xl border border-border bg-card/80"
      aria-labelledby="mobile-bridge-title"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 p-4">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-signal/15 text-signal">
            <Smartphone className="size-5" />
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-signal">
              Android companion bridge
            </p>
            <h2 id="mobile-bridge-title" className="text-base font-semibold">
              Mobile Executive Bridge
            </h2>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void refresh()}
          disabled={loading}
          aria-label="Refresh mobile bridge"
        >
          <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>
      <div className="grid gap-2 p-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border/70 bg-background/40 p-3">
          <p className="text-[10px] uppercase text-muted-foreground">Companion</p>
          <p
            className={`mt-2 text-sm font-semibold ${status?.available ? "text-ok" : "text-warn"}`}
          >
            {status?.available ? "Bridge ready" : "Not connected"}
          </p>
          <p className="mt-1 truncate text-[11px] text-muted-foreground">
            {status?.package ?? "com.nous.companion"}
          </p>
        </div>
        <div className="rounded-xl border border-border/70 bg-background/40 p-3">
          <p className="text-[10px] uppercase text-muted-foreground">Live commands</p>
          <p className="mt-2 text-sm font-semibold">{status?.commands?.length ?? 0} available</p>
          <p className="mt-1 text-[11px] text-muted-foreground">Accessibility service</p>
        </div>
        <div className="rounded-xl border border-border/70 bg-background/40 p-3">
          <p className="text-[10px] uppercase text-muted-foreground">Pending approvals</p>
          <p className="mt-2 text-sm font-semibold text-warn">{approvals.length}</p>
          <p className="mt-1 text-[11px] text-muted-foreground">Tap to resolve</p>
        </div>
      </div>
      {approvals.length > 0 && (
        <div className="border-t border-border/70 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold">
            <CircleAlert className="size-4 text-warn" />
            Instant action approvals
          </div>
          <div className="space-y-2">
            {approvals.map((approval) => (
              <div
                key={approval.id}
                className="flex flex-wrap items-center gap-2 rounded-xl border border-warn/20 bg-warn/5 p-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{approval.tool}</p>
                  <p className="text-[11px] text-muted-foreground">
                    {approval.missionId
                      ? `Mission ${approval.missionId}`
                      : "Requires your approval"}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void resolveApproval(approval.id, "rejected")}
                  disabled={busy === approval.id}
                >
                  <X className="size-3.5" />
                  Reject
                </Button>
                <Button
                  size="sm"
                  onClick={() => void resolveApproval(approval.id, "approved")}
                  disabled={busy === approval.id}
                >
                  {busy === approval.id ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Check className="size-3.5" />
                  )}
                  Approve
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
