import { Link } from "@tanstack/react-router";

import { ChatMarkdown } from "@/components/nous/chat-markdown";
import { sectionConfigs } from "@/components/nous/section-configs";
import { SectionPanel } from "@/components/nous/section-panel";
import { MissionList } from "@/components/nous/mission-list";
import { ApprovalList } from "@/components/nous/approval-list";
import { HealthPanel } from "@/components/nous/health-panel";
import { summarizeMissions } from "@/components/nous/mission-status";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";
import { stripMarkdown } from "@/lib/strip-markdown";
import {
  Activity,
  ArrowUpRight,
  Loader2,
  Mic,
  MicOff,
  ThumbsDown,
  ThumbsUp,
  Volume2,
  VolumeX,
  Menu,
  RotateCcw,
  ScanLine,
  Send,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Square,
  X,
  UploadCloud,
  Home,
  MessageSquare,
  Target,
  ClipboardList,
  Library,
  Settings,
  CheckCircle2,
  Brain,
  CircleDot,
  Search,
} from "lucide-react";
import { navGroups, navLabel } from "@/components/nous/nav";
import {
  clearNousToken,
  getNousToken,
  hasConfiguredNousApi,
  hasStoredNousToken,
  nousFetch,
  setNousToken,
} from "@/lib/nous-api";

import { Button } from "@/components/ui/button";
import { Card, DocumentStat, Metric, NavGlyph, NavButton, StatBar } from "./dashboard-primitives";
import type { useDashboard } from "./use-dashboard";
import { ConnectionSettings } from "./dashboard-connection-settings";

export function DashboardSidebar({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
const { section, advancedOpen, setAdvancedOpen, menuOpen, setMenuOpen, systemStatus, go } = dashboard;
return (<>
        {/* Sidebar */}
        {menuOpen && (
          <button
            aria-label="Κλείσε το μενού"
            onClick={() => setMenuOpen(false)}
            className="fixed inset-0 z-40 bg-black/55 lg:hidden"
          />
        )}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-card/95 transition-transform lg:static lg:translate-x-0 ${
            menuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex items-start justify-between px-4 pb-3 pt-4">
            <div>
              <p className="font-display text-base font-bold tracking-tight">🧠 NOUS AI OS</p>
              <p className="mt-0.5 text-xs text-muted-foreground">Personal agent workspace</p>
            </div>
            <button
              onClick={() => setMenuOpen(false)}
              className="text-muted-foreground lg:hidden"
              aria-label="Κλείσε"
            >
              <X className="size-4" />
            </button>
          </div>

          <nav className="flex-1 overflow-y-auto px-2 pb-2">
            {navGroups
              .filter((g) => !g.advanced)
              .map((group, gi) => (
                <div key={group.title ?? gi}>
                  {group.title && (
                    <p className="px-2.5 pb-1 pt-3 font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                      {group.title}
                    </p>
                  )}
                  {group.items.map((item) => (
                    <NavButton
                      key={item.id}
                      item={item}
                      active={section === item.id}
                      onClick={() => go(item.id)}
                    />
                  ))}
                  {gi === 0 && <div className="my-2 h-px bg-border" />}
                </div>
              ))}

            <div className="my-2 h-px bg-border" />
            <button
              onClick={() => setAdvancedOpen((o) => !o)}
              className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground"
            >
              ⋯ Προχωρημένα
              <span className="ml-auto text-[10px]">{advancedOpen ? "▾" : "▸"}</span>
            </button>
            {advancedOpen &&
              navGroups
                .filter((g) => g.advanced)
                .map((group) => (
                  <div key={group.title}>
                    <p className="px-2.5 pb-1 pt-3 font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                      {group.title}
                    </p>
                    {group.items.map((item) => (
                      <NavButton
                        key={item.id}
                        item={item}
                        active={section === item.id}
                        onClick={() => go(item.id)}
                      />
                    ))}
                  </div>
                ))}
          </nav>

          <div className="border-t border-border px-3 py-3">
            <StatBar
              label="CPU"
              pct={Math.round(systemStatus?.metrics?.cpu_percent ?? 0)}
              color="bg-violet"
            />
            <StatBar
              label="RAM"
              pct={Math.round(systemStatus?.metrics?.memory_percent ?? 0)}
              color="bg-primary"
            />
          </div>
        </aside>


</>);
}
