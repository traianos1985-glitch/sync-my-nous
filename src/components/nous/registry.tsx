import { ChatSection } from "@/components/nous/sections/chat";
import { HomeSection } from "@/components/nous/sections/home";
import {
  AppBuilderSection,
  BrainSection,
  GoalsSection,
  MissionsSection,
  PlannerSection,
} from "@/components/nous/sections/work";
import {
  BackupSection,
  DeploySection,
  DocumentsSection,
  SchedulerSection,
  SettingsSection,
} from "@/components/nous/sections/tools";
import {
  AnalystSection,
  ApprovalsSection,
  CommandSection,
  GraphsSection,
  ModuleSection,
  PendingSection,
  SystemMonitorSection,
} from "@/components/nous/sections/system";
import { actions, useNous } from "@/lib/store";
import { Badge, Card, GhostButton, SectionHeader } from "@/components/nous/ui";

type ModuleMeta = { label: string; description: string; tips: string[] };

const MODULE_META: Record<string, ModuleMeta> = {
  autoexec: {
    label: "Auto Exec",
    description: "Αυτόνομη εκτέλεση εγκεκριμένων εργασιών χωρίς χειροκίνητη παρέμβαση.",
    tips: [
      "Παίρνει missions από την ουρά και τα τρέχει σειριακά.",
      "Σέβεται τα όρια πόρων και τα guardrails ασφαλείας.",
      "Καταγράφει κάθε βήμα στο journal.",
    ],
  },
  loopv3: {
    label: "Agent Loop",
    description: "Ο βρόχος σκέψη → σχεδιασμός → δράση → αναθεώρηση του agent.",
    tips: [
      "Επαναλαμβάνει τον κύκλο μέχρι να επιτευχθεί ο στόχος.",
      "Χρησιμοποιεί τη μνήμη για συνέχεια μεταξύ κύκλων.",
      "Σταματά αυτόματα σε αβεβαιότητα και ζητά έγκριση.",
    ],
  },
  autoscheduler: {
    label: "AutoSched",
    description: "Αυτόματος προγραμματισμός επαναλαμβανόμενων εργασιών.",
    tips: [
      "Δημιουργεί cron jobs με βάση τα μοτίβα χρήσης.",
      "Βελτιστοποιεί τις ώρες εκτέλεσης για χαμηλό φορτίο.",
    ],
  },
  diagnosis: {
    label: "Diagnosis",
    description: "Διάγνωση προβλημάτων στον κώδικα και στο runtime.",
    tips: [
      "Σαρώνει logs και stack traces για ανωμαλίες.",
      "Εντοπίζει τη ρίζα του προβλήματος.",
      "Παράγει αναφορά με προτεινόμενες διορθώσεις.",
    ],
  },
  repair: {
    label: "Repair",
    description: "Αυτόματη επιδιόρθωση εντοπισμένων βλαβών.",
    tips: [
      "Εφαρμόζει repair proposals μετά από έγκριση.",
      "Κρατά backup πριν από κάθε αλλαγή.",
    ],
  },
  selfheal: {
    label: "Self Heal",
    description: "Συνεχής παρακολούθηση και αυτό-επούλωση του συστήματος.",
    tips: [
      "Επανεκκινεί υπηρεσίες που κρασάρουν.",
      "Καθαρίζει διαρροές μνήμης και κολλημένα jobs.",
    ],
  },
  intelligence: {
    label: "Intelligence",
    description: "Συγκέντρωση και σύνθεση πληροφορίας από πολλές πηγές.",
    tips: [
      "Συνδυάζει μνήμη, έγγραφα και web research.",
      "Παράγει περιλήψεις και insights.",
    ],
  },
  learning: {
    label: "Learning",
    description: "Ο agent μαθαίνει από τα αποτελέσματα και τα λάθη του.",
    tips: [
      "Ενημερώνει τη decision memory μετά από κάθε mission.",
      "Προσαρμόζει στρατηγικές με βάση την επιτυχία.",
    ],
  },
  audit: {
    label: "Audit",
    description: "Έλεγχος ασφαλείας και ακεραιότητας των ενεργειών.",
    tips: [
      "Καταγράφει κάθε προνομιακή ενέργεια.",
      "Επαληθεύει ότι κάθε endpoint έχει token (fail-closed).",
    ],
  },
  companion: {
    label: "Companion",
    description: "Android companion με accessibility service για έλεγχο κινητού.",
    tips: [
      "Εκτελεί ασφαλείς εντολές στη συσκευή.",
      "Συγχρονίζεται με το κύριο service μέσω token.",
    ],
  },
  larmor: {
    label: "Larmor Monitor",
    description: "Παρακολούθηση σημάτων και συχνοτήτων του περιβάλλοντος.",
    tips: [
      "Καταγράφει μετρήσεις σε πραγματικό χρόνο.",
      "Ειδοποιεί σε ανωμαλίες εκτός ορίων.",
    ],
  },
  field: {
    label: "Πεδίο & Χάρτης",
    description: "Χωρική επισκόπηση των ενεργών operators και δεδομένων.",
    tips: [
      "Οπτικοποιεί την κατάσταση των operators.",
      "Συνδέει γεωγραφικά δεδομένα με missions.",
    ],
  },
  "remote-access": {
    label: "Remote Access",
    description: "Ασφαλής απομακρυσμένη πρόσβαση στο service μέσω token.",
    tips: [
      "Δημιούργησε token με POST /token/create.",
      "Στείλε το ως X-NOUS-TOKEN σε κάθε αίτημα.",
      "Χωρίς token επιτρέπεται μόνο localhost.",
    ],
  },
};

const ROADMAP = [
  { title: "Ενοποίηση agent modules σε ένα core", priority: "Π1" },
  { title: "Σύγχρονο web UI (αυτό το workspace)", priority: "Π1", done: true },
  { title: "Βάση δεδομένων αντί για JSON αρχεία", priority: "Π2" },
  { title: "Streaming απαντήσεις & queue", priority: "Π2", done: true },
  { title: "Παρατηρησιμότητα & κόστος ανά κλήση", priority: "Π3" },
  { title: "Πραγματικά tests αντί για smoke", priority: "Π3" },
];

function UpgradesSection() {
  const { goals } = useNous();
  const has = (t: string) => goals.some((g) => g.title === t);

  return (
    <div className="p-4 md:p-6">
      <SectionHeader title="Upgrades" subtitle="Roadmap αναβαθμίσεων — μετέτρεψε μια πρόταση σε στόχο." />
      <div className="grid gap-3 md:grid-cols-2">
        {ROADMAP.map((u) => (
          <Card key={u.title}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <Badge tone={u.priority === "Π1" ? "err" : u.priority === "Π2" ? "warn" : "muted"}>{u.priority}</Badge>
                  {u.done && <Badge tone="ok">υλοποιήθηκε</Badge>}
                </div>
                <h3 className="mt-2 font-display text-base font-semibold">{u.title}</h3>
              </div>
            </div>
            {!u.done && (
              <GhostButton
                className="mt-3"
                active={has(u.title)}
                onClick={() => !has(u.title) && actions.addGoal(u.title, "Από το roadmap αναβαθμίσεων")}
              >
                {has(u.title) ? "Προστέθηκε στους στόχους" : "Κάν' το στόχο"}
              </GhostButton>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

export function SectionRenderer({
  section,
  onNavigate,
}: {
  section: string;
  onNavigate: (id: string) => void;
}) {
  switch (section) {
    case "chat":
      return <ChatSection />;
    case "home":
      return <HomeSection onNavigate={onNavigate} />;
    case "goals":
      return <GoalsSection />;
    case "missions":
      return <MissionsSection />;
    case "planner":
      return <PlannerSection />;
    case "brain":
      return <BrainSection />;
    case "appbuilder":
      return <AppBuilderSection />;
    case "documents":
      return <DocumentsSection />;
    case "scheduler":
      return <SchedulerSection />;
    case "deploy":
      return <DeploySection />;
    case "backup":
      return <BackupSection />;
    case "settings":
      return <SettingsSection />;
    case "approvals":
      return <ApprovalsSection />;
    case "pending":
      return <PendingSection />;
    case "command":
      return <CommandSection />;
    case "system":
      return <SystemMonitorSection />;
    case "graphs":
      return <GraphsSection />;
    case "analyst":
      return <AnalystSection />;
    case "upgrades":
      return <UpgradesSection />;
    default: {
      const meta = MODULE_META[section];
      if (meta) {
        return <ModuleSection id={section} label={meta.label} description={meta.description} tips={meta.tips} />;
      }
      return <ModuleSection id={section} label={section} description="Module του NOUS AI OS." tips={["Πάτησε «Εκτέλεση» για να το τρέξεις."]} />;
    }
  }
}
