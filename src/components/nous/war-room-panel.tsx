import { useState, type FormEvent } from "react";
import { ArrowRight, Bot, CheckCircle2, Loader2, ShieldCheck, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { nousFetch } from "@/lib/nous-api";

type Delegation = {
  role: string;
  title: string;
  task: string;
  status: "queued" | "ready";
};

type DelegationResponse = {
  goal: string;
  status: string;
  approval_required: boolean;
  delegations: Delegation[];
};

const defaultGoal =
  "Ερεύνησε τις τιμές εξοπλισμού, φτιάξε web app σύγκρισης και ανέβασέ το στο sandbox";

export function WarRoomPanel() {
  const [goal, setGoal] = useState("");
  const [plan, setPlan] = useState<DelegationResponse | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");

  async function delegate(event: FormEvent) {
    event.preventDefault();
    const objective = goal.trim();
    if (!objective) return;
    setStatus("loading");
    setPlan(null);
    try {
      const result = await nousFetch<DelegationResponse>("/remote/team/delegate", {
        method: "POST",
        body: JSON.stringify({ goal: objective }),
        timeoutMs: 90_000,
      });
      setPlan(result);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  return (
    <section
      className="mb-5 overflow-hidden rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 via-card/70 to-signal/5"
      aria-labelledby="war-room-title"
    >
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border/60 p-4">
        <div className="flex gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Users className="size-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary">
                Multi-agent war room
              </p>
              <span className="rounded-full border border-ok/30 bg-ok/10 px-2 py-0.5 font-mono text-[9px] text-ok">
                READY
              </span>
            </div>
            <h2 id="war-room-title" className="mt-1 text-lg font-semibold">
              Δώσε έναν στόχο. Ο NOUS αναθέτει την εκτέλεση.
            </h2>
            <p className="mt-1 max-w-2xl text-xs text-muted-foreground">
              Planner, Research, Builder και Reviewer συνεργάζονται με guardian gate πριν από κάθε
              εξωτερική ενέργεια.
            </p>
          </div>
        </div>
        <ShieldCheck className="size-5 text-ok" aria-label="Approval gate enabled" />
      </div>

      <form onSubmit={delegate} className="flex flex-col gap-2 p-4 sm:flex-row">
        <label className="sr-only" htmlFor="war-room-goal">
          Στόχος αποστολής
        </label>
        <input
          id="war-room-goal"
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          placeholder={defaultGoal}
          maxLength={2000}
          className="min-w-0 flex-1 rounded-xl border border-border bg-background/70 px-3 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-primary"
        />
        <Button
          type="submit"
          disabled={status === "loading" || !goal.trim()}
          className="rounded-xl px-4"
        >
          {status === "loading" ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <ArrowRight className="size-4" />
          )}
          <span>Ξεκίνα War Room</span>
        </Button>
      </form>

      {status === "error" && (
        <p role="alert" className="px-4 pb-4 text-xs text-destructive">
          Δεν ήταν δυνατή η δημιουργία πλάνου. Έλεγξε τη σύνδεση και το NOUS token.
        </p>
      )}
      {plan && (
        <div className="border-t border-border/60 p-4">
          <div className="mb-3 flex items-center justify-between gap-2 text-xs">
            <span className="font-medium">
              Πλάνο ανάθεσης για: <span className="text-muted-foreground">{plan.goal}</span>
            </span>
            <span className="font-mono uppercase text-ok">{plan.status}</span>
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            {plan.delegations.map((item) => (
              <div
                key={item.role}
                className="rounded-xl border border-border/70 bg-background/50 p-3"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="size-4 text-ok" />
                  <span className="text-sm font-semibold">{item.title}</span>
                  <Bot className="ml-auto size-3.5 text-muted-foreground" />
                </div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.task}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] text-muted-foreground">
            Το πλάνο είναι έτοιμο για εκτέλεση. Ενέργειες με side effects παραμένουν σε approval
            queue.
          </p>
        </div>
      )}
    </section>
  );
}
