import { Check, X, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { canApproveRepair, type RepairDetail } from "./app-studio-model";

export function StudioRepair({
  detail,
  busy,
  onResolve,
}: {
  detail: RepairDetail;
  busy: boolean;
  onResolve: (approve: boolean) => void;
}) {
  return (
    <section className="min-w-0 space-y-4" aria-label="Έλεγχος επισκευής">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 font-semibold">
          <ShieldCheck className="size-4 text-primary" />
          Self-Healing review
        </h3>
        <span className="font-mono text-xs text-warn">{detail.proposal.status}</span>
      </div>
      <p className="text-sm">{detail.proposal.summary}</p>
      {detail.proposal.root_causes?.map((cause, i) => (
        <pre key={i} className="whitespace-pre-wrap break-words text-xs text-muted-foreground">
          {typeof cause === "string" ? cause : JSON.stringify(cause, null, 2)}
        </pre>
      ))}
      {[...detail.review.blockers, ...detail.review.warnings, ...(detail.proposal.risks ?? [])].map(
        (text, i) => (
          <p key={i} className="break-words text-xs text-warn">
            {text}
          </p>
        ),
      )}
      {detail.changes.map((change) => (
        <details key={change.path} open>
          <summary className="cursor-pointer break-all font-mono text-xs text-primary">
            {change.path}
          </summary>
          <pre className="mt-2 max-h-96 overflow-auto border border-border bg-background p-3 font-mono text-xs">
            {change.diff.split("\n").map((line, i) => (
              <div
                key={i}
                className={
                  line.startsWith("+")
                    ? "text-ok bg-ok/5"
                    : line.startsWith("-")
                      ? "text-destructive bg-destructive/5"
                      : "text-muted-foreground"
                }
              >
                {line || " "}
              </div>
            ))}
          </pre>
        </details>
      ))}
      {detail.proposal.validation_plan?.length ? (
        <ul className="space-y-1 text-xs text-muted-foreground">
          {detail.proposal.validation_plan.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ul>
      ) : null}
      {detail.proposal.status === "pending_review" && (
        <div className="flex flex-wrap gap-2">
          <Button
            disabled={busy || !canApproveRepair(detail)}
            onClick={() => {
              if (
                window.confirm(
                  "Να εφαρμοστούν οι αλλαγές που εμφανίζονται; Τα tests θα χρειαστούν νέα εκτέλεση.",
                )
              )
                onResolve(true);
            }}
          >
            <Check className="size-4" />
            Έγκριση και εφαρμογή
          </Button>
          <Button variant="outline" disabled={busy} onClick={() => onResolve(false)}>
            <X className="size-4" />
            Απόρριψη
          </Button>
        </div>
      )}
    </section>
  );
}
