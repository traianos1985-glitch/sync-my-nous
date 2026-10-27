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

export function DashboardCommandMenu({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
const { section, commandOpen, setCommandOpen, chatInputRef, loadSystemStatus, go, commandItems } = dashboard;
return (<>
      <CommandDialog open={commandOpen} onOpenChange={setCommandOpen}>
        <CommandInput placeholder="Αναζήτηση στο workspace…" />
        <CommandList>
          <CommandEmpty>Δεν βρέθηκε ενότητα.</CommandEmpty>
          <CommandGroup heading="Πλοήγηση">
            {commandItems.map((item) => (
              <CommandItem
                key={item.id}
                value={`${item.label} ${item.id}`}
                onSelect={() => {
                  go(item.id);
                  setCommandOpen(false);
                }}
              >
                <NavGlyph name={item.icon} />
                <span>{item.label}</span>
                {item.id === section && <CommandShortcut>active</CommandShortcut>}
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandGroup heading="Γρήγορες ενέργει����ς">
            <CommandItem
              value="new message chat"
              onSelect={() => {
                go("chat");
                setCommandOpen(false);
                window.requestAnimationFrame(() => chatInputRef.current?.focus());
              }}
            >
              <MessageSquare />
              <span>Νέο μήνυμα στον NOUS</span>
              <CommandShortcut>↵</CommandShortcut>
            </CommandItem>
            <CommandItem
              value="refresh system health"
              onSelect={() => {
                void loadSystemStatus();
                setCommandOpen(false);
              }}
            >
              <RotateCcw />
              <span>Ανανέωση health status</span>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>

</>);
}
