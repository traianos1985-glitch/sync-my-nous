import { useDashboard } from "./use-dashboard";
import { DashboardChat } from "./dashboard-chat";
import { DashboardHome } from "./dashboard-home";
import { DashboardWorkspace } from "./dashboard-workspace";
import { DashboardCommandMenu } from "./dashboard-command-menu";
import { DashboardSidebar } from "./dashboard-sidebar";
import { DashboardHeader } from "./dashboard-header";
import { BackendWakeBanner } from "./backend-wake-banner";
import { ShortcutsDialog } from "./shortcuts-dialog";

export function Dashboard({ sessionId }: { sessionId?: string }) {
  const dashboard = useDashboard(sessionId);
  return (
    <>
      <DashboardCommandMenu dashboard={dashboard} />
      <ShortcutsDialog open={dashboard.shortcutsOpen} onOpenChange={dashboard.setShortcutsOpen} />
      <div className="flex h-dvh min-h-0 w-full min-w-0 max-w-full overflow-hidden bg-background font-sans text-foreground">
        <DashboardSidebar dashboard={dashboard} />
        <main className="flex min-w-0 max-w-full flex-1 flex-col">
          <BackendWakeBanner onRetry={() => void dashboard.loadSystemStatus()} />
          <DashboardHeader dashboard={dashboard} />
          {dashboard.section === "chat" ? (
            <DashboardChat dashboard={dashboard} />
          ) : dashboard.section === "home" ? (
            <DashboardHome dashboard={dashboard} />
          ) : (
            <DashboardWorkspace dashboard={dashboard} />
          )}
        </main>
      </div>
    </>
  );
}
