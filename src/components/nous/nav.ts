// Το menu του NOUS AI OS — ίδιο με το dashboard της Flask εφαρμογής.
// Πρόσθεσε / άλλαξε items ελεύθερα: το UI προσαρμόζεται αυτόματα.

export type NavItem = { id: string; icon: string; label: string };
export type NavGroup = { title?: string; items: NavItem[]; advanced?: boolean };

export const navGroups: NavGroup[] = [
  {
    items: [
      { id: "chat", icon: "💬", label: "Chat" },
      { id: "home", icon: "🏠", label: "Dashboard" },
    ],
  },
  {
    title: "Εργασία",
    items: [
      { id: "goals", icon: "🎯", label: "Goals" },
      { id: "missions", icon: "📋", label: "Missions" },
      { id: "planner", icon: "🧩", label: "Planner" },
      { id: "brain", icon: "🧠", label: "Brain & Memory" },
      { id: "appbuilder", icon: "🏗", label: "App Builder" },
    ],
  },
  {
    title: "Εργαλεία",
    items: [
      { id: "documents", icon: "📚", label: "Documents" },
      { id: "scheduler", icon: "⏱", label: "Scheduler" },
      { id: "deploy", icon: "🚀", label: "Deploy" },
      { id: "backup", icon: "☁", label: "Backup" },
      { id: "larmor", icon: "🧲", label: "Larmor Monitor" },
      { id: "field", icon: "🔍", label: "Πεδίο & Χάρτης" },
      { id: "remote-access", icon: "📡", label: "Remote Access" },
      { id: "settings", icon: "⚙", label: "Settings" },
    ],
  },
  {
    title: "Αυτοματισμός",
    advanced: true,
    items: [
      { id: "autoexec", icon: "🤖", label: "Auto Exec" },
      { id: "loopv3", icon: "♾", label: "Agent Loop" },
      { id: "autoscheduler", icon: "🔁", label: "AutoSched" },
    ],
  },
  {
    title: "Σύστημα",
    advanced: true,
    items: [
      { id: "diagnosis", icon: "🩺", label: "Diagnosis" },
      { id: "repair", icon: "🛠", label: "Repair" },
      { id: "selfheal", icon: "🧬", label: "Self Heal" },
      { id: "intelligence", icon: "🧭", label: "Intelligence" },
      { id: "learning", icon: "🎓", label: "Learning" },
      { id: "system", icon: "📊", label: "System" },
      { id: "command", icon: "⌨", label: "Command" },
      { id: "approvals", icon: "✅", label: "Approvals" },
      { id: "audit", icon: "🧪", label: "Audit" },
      { id: "companion", icon: "📱", label: "Companion" },
      { id: "pending", icon: "📥", label: "Pending" },
      { id: "graphs", icon: "🕸", label: "Graphs" },
      { id: "analyst", icon: "🧮", label: "Analyst" },
      { id: "upgrades", icon: "📦", label: "Upgrades" },
    ],
  },
];

export const navLabel = (id: string) =>
  navGroups.flatMap((g) => g.items).find((i) => i.id === id)?.label ?? id;
