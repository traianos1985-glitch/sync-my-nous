import { Button } from "@/components/ui/button";
import {
  Home,
  MessageSquare,
  Target,
  ClipboardList,
  Library,
  Settings,
  CheckCircle2,
  Brain,
  CircleDot,
} from "lucide-react";
export function NavGlyph({ name }: { name: string }) {
  const icons: Record<string, typeof CircleDot> = {
    message: MessageSquare,
    home: Home,
    target: Target,
    clipboard: ClipboardList,
    library: Library,
    settings: Settings,
    check: CheckCircle2,
    brain: Brain,
  };
  const Icon = icons[name] ?? CircleDot;
  return <Icon aria-hidden="true" className="size-4 shrink-0 text-current" />;
}

export function NavButton({
  item,
  active,
  onClick,
}: {
  item: { icon: string; label: string };
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      variant="ghost"
      onClick={onClick}
      className={`my-0.5 flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors ${
        active
          ? "bg-violet/20 font-semibold text-foreground"
          : "text-muted-foreground hover:bg-violet/10 hover:text-foreground"
      }`}
    >
      <NavGlyph name={item.icon} />
      {item.label}
    </Button>
  );
}

export function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="min-w-0 max-w-full rounded-2xl border border-border bg-card p-5">
      <h3 className="mb-3 font-display text-base font-semibold">{title}</h3>
      {children}
    </section>
  );
}

export function DocumentStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-border/70 bg-background/50 p-3">
      <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-mono text-lg font-semibold text-primary">{value}</p>
    </div>
  );
}

export function StatBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  const safePct = Math.min(100, Math.max(0, pct));
  return (
    <div className="flex items-center gap-2 py-1 font-mono text-[11px] text-muted-foreground">
      <span className="w-8">{label}</span>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-muted">
        <div className={`h-full ${color}`} style={{ width: `${safePct}%` }} />
      </div>
      <span>{safePct}%</span>
    </div>
  );
}

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-card/60 p-2 text-center">
      <div className="font-mono text-sm text-foreground">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}
