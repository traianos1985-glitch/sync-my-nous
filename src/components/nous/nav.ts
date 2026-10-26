// Το menu του NOUS AI OS — ίδιο με το dashboard της Flask εφαρμογής.
// Πρόσθεσε / άλλαξε items ελεύθερα: το UI προσαρμόζεται αυτόματα.

export type NavItem = { id: string; icon: string; label: string };
export type NavGroup = { title?: string; items: NavItem[]; advanced?: boolean };

export const navGroups: NavGroup[] = [
  {
    items: [
      { id: "chat", icon: "message", label: "Chat" },
      { id: "home", icon: "home", label: "Dashboard" },
    ],
  },
  {
    title: "Εργασία",
    items: [
      { id: "goals", icon: "target", label: "Goals" },
      { id: "missions", icon: "clipboard", label: "Missions" },
      { id: "planner", icon: "planner", label: "Planner" },
      { id: "brain", icon: "brain", label: "Brain & Memory" },
      { id: "appbuilder", icon: "appbuilder", label: "App Builder" },
    ],
  },
  {
    title: "Εργαλεία",
    items: [
      { id: "documents", icon: "library", label: "Documents" },
      { id: "scheduler", icon: "scheduler", label: "Scheduler" },
      { id: "deploy", icon: "deploy", label: "Deploy" },
      { id: "backup", icon: "backup", label: "Backup" },
      { id: "larmor", icon: "larmor", label: "Larmor Monitor" },
      { id: "techwatch", icon: "techwatch", label: "Tech Watch" },
      { id: "field", icon: "field", label: "Πεδίο & Χάρτης" },
      { id: "remote-access", icon: "remote-access", label: "Remote Access" },
      { id: "control", icon: "◈", label: "Control Plane" },
      { id: "settings", icon: "settings", label: "Settings" },
    ],
  },
  {
    title: "Αυτοματισμός",
    advanced: true,
    items: [
      { id: "autoexec", icon: "autoexec", label: "Auto Exec" },
      { id: "loopv3", icon: "loopv3", label: "Agent Loop" },
      { id: "autoscheduler", icon: "autoscheduler", label: "AutoSched" },
    ],
  },
  {
    title: "Σύστημα",
    advanced: true,
    items: [
      { id: "diagnosis", icon: "diagnosis", label: "Diagnosis" },
      { id: "bootstrap", icon: "bootstrap", label: "Environment Bootstrap" },
      { id: "repair", icon: "repair", label: "Repair" },
      { id: "selfheal", icon: "selfheal", label: "Self Heal" },
      { id: "intelligence", icon: "intelligence", label: "Intelligence" },
      { id: "learning", icon: "learning", label: "Learning" },
      { id: "system", icon: "system", label: "System" },
      { id: "command", icon: "command", label: "Command" },
      { id: "approvals", icon: "check", label: "Approvals" },
      { id: "audit", icon: "audit", label: "Audit" },
      { id: "companion", icon: "companion", label: "Companion" },
      { id: "pending", icon: "pending", label: "Pending" },
      { id: "graphs", icon: "graphs", label: "Graphs" },
      { id: "analyst", icon: "analyst", label: "Analyst" },
      { id: "upgrades", icon: "upgrades", label: "Upgrades" }
    ],
  },
];

export const navLabel = (id: string) =>
  navGroups.flatMap((g) => g.items).find((i) => i.id === id)?.label ?? id;
