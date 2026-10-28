import { Link } from "@tanstack/react-router";

import { Menu, RotateCcw, Search, Keyboard } from "lucide-react";
import { navLabel } from "@/components/nous/nav";

import { Button } from "@/components/ui/button";

import type { useDashboard } from "./use-dashboard";
import { ChatHistoryDrawer } from "./chat-history-drawer";

export function DashboardHeader({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const {
    section,
    setMenuOpen,
    setCommandOpen,
    setShortcutsOpen,
    approvals,
    systemStatus,
    systemStatusState,
    systemStatusCheckedAt,
    systemStatusError,
    loadSystemStatus,
    go,
  } = dashboard;

  return (
    <>
      <header className="flex min-w-0 shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border/70 bg-card/70 px-4 py-3 backdrop-blur-xl">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            onClick={() => setMenuOpen(true)}
            className="rounded-md border border-border p-1.5 lg:hidden"
            aria-label="Άνοιξε το μενού"
          >
            <Menu className="size-4" />
          </Button>
          <strong className="font-display text-sm">{navLabel(section)}</strong>
          <Button
            variant="ghost"
            type="button"
            onClick={() => setCommandOpen(true)}
            className="hidden min-w-44 items-center justify-between gap-3 rounded-lg border border-border/70 bg-background/50 px-2.5 py-1.5 text-left text-xs text-muted-foreground transition hover:border-primary/50 hover:text-foreground sm:flex"
            aria-label="Άνοιγμα command search"
          >
            <span className="inline-flex items-center gap-2">
              <Search className="size-3.5" /> Αναζήτηση…
            </span>
            <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px]">
              ⌘K
            </kbd>
          </Button>

          {approvals.length > 0 && (
            <Button
              variant="ghost"
              type="button"
              onClick={() => go("approvals")}
              aria-label="Εκκρεμείς εγκρίσεις"
              title={`${approvals.length} ${approvals.length === 1 ? "έγκριση σε εκκρεμότητα" : "εγκρίσεις σε εκκρεμότητα"}`}
              className="flex items-center gap-1.5 rounded-full border border-warn/40 bg-warn/10 px-2.5 py-0.5 text-xs font-semibold text-warn hover:bg-warn/20"
            >
              <span className="size-1.5 rounded-full bg-warn animate-pulse" />
              <span>
                {approvals.length} {approvals.length === 1 ? "έγκριση" : "εγκρίσεις"}
              </span>
            </Button>
          )}

          <span
            title={systemStatusError ?? undefined}
            className={`rounded-full border border-border px-2.5 py-0.5 font-mono text-xs ${systemStatus?.status === "degraded" || systemStatus?.status === "unavailable" ? "text-warn" : "text-ok"}`}
          >
            health: {systemStatus?.status ?? "checking"}
          </span>
          <Button
            variant="ghost"
            type="button"
            onClick={() => void loadSystemStatus()}
            disabled={systemStatusState === "loading"}
            aria-label="Ανανέωση health status"
            title={
              systemStatusCheckedAt
                ? `Τελευταίος έλεγχος ${new Date(systemStatusCheckedAt).toLocaleTimeString("el-GR")}`
                : "Ανανέωση health status"
            }
            className="rounded-md border border-border p-1.5 text-muted-foreground transition hover:bg-accent hover:text-foreground disabled:opacity-50"
          >
            <RotateCcw
              className={`size-3.5 ${systemStatusState === "loading" ? "animate-spin" : ""}`}
            />
          </Button>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <ChatHistoryDrawer dashboard={dashboard} />
          <Button
            variant="ghost"
            type="button"
            onClick={() => setShortcutsOpen(true)}
            aria-label="Οδηγός συντομεύσεων πληκτρολογίου"
            title="Συντομεύσεις πληκτρολογίου (?)"
            className="hidden size-8 items-center justify-center rounded-lg border border-border p-0 text-muted-foreground transition hover:bg-accent hover:text-foreground sm:inline-flex"
          >
            <Keyboard className="size-4" />
          </Button>
          <Button
            variant="ghost"
            type="button"
            onClick={() => go("settings")}
            aria-label="Άνοιγμα Settings και ρυθμίσεων σύνδεσης"
            title="Ρυθμίσεις σύνδεσης NOUS"
            className="inline-flex items-center gap-1.5 rounded-lg border border-primary/40 bg-primary/5 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/10"
          >
            ⚙ Settings
          </Button>
          <span className="hidden rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-muted-foreground sm:block">
            Owner Mode
          </span>
          <Link
            to="/"
            className="rounded-full border border-border px-2.5 py-0.5 font-mono text-xs text-primary hover:bg-accent"
          >
            info
          </Link>
        </div>
      </header>
    </>
  );
}
