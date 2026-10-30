import { useState } from "react";
import {
  Play,
  Square,
  Download,
  RefreshCw,
  FlaskConical,
  Wrench,
  Loader2,
  Terminal,
  FileCode2,
  Check,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAppStudio } from "./use-app-studio";
import { StudioFiles } from "./app-studio-files";
import { StudioRepair } from "./app-studio-repair";

export function AppBuilderStudio({ connected }: { connected: boolean }) {
  const studio = useAppStudio(connected);
  const [description, setDescription] = useState("");
  const [filter, setFilter] = useState("");
  const [tab, setTab] = useState("code");
  const app = studio.apps.find((item) => item.name === studio.selected);
  const disabled = Boolean(studio.busy) || !connected;
  return (
    <div className="min-w-0 flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mx-auto min-w-0 max-w-7xl space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-mono text-xs text-primary">NOUS / ENGINEERING</p>
            <h1 className="mt-1 text-2xl font-semibold">App Builder Studio</h1>
          </div>
          <Button
            variant="outline"
            size="icon"
            aria-label="Ανανέωση εφαρμογών"
            title="Ανανέωση"
            disabled={studio.loading || disabled}
            onClick={() => void studio.refresh()}
          >
            <RefreshCw className={studio.loading ? "size-4 animate-spin" : "size-4"} />
          </Button>
        </header>
        {!connected && (
          <p role="status" className="border-l-2 border-warn pl-3 text-sm text-warn">
            Βάλε το NOUS token στις Ρυθμίσεις για να φορτωθούν οι εφαρμογές.
          </p>
        )}
        {studio.error && (
          <p
            role="alert"
            className="break-words border-l-2 border-destructive pl-3 text-sm text-destructive"
          >
            {studio.error}
          </p>
        )}
        <form
          className="flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void studio.plan(description);
          }}
        >
          <Input
            className="min-w-0 flex-1 basis-64"
            aria-label="Περιγραφή νέας εφαρμογής"
            placeholder="Νέα εφαρμογή…"
            maxLength={8000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button disabled={disabled || !description.trim()} type="submit">
            {studio.busy === "plan" && <Loader2 className="size-4 animate-spin" />}Δημιουργία
            σχεδίου
          </Button>
        </form>
        {studio.builds
          .filter((build) => build.status === "pending_approval")
          .map((build) => (
            <details key={build.plan_id} className="border-y border-border py-3">
              <summary className="cursor-pointer text-sm">
                {build.title ?? build.app_name} <span className="text-warn">· προς έγκριση</span>
              </summary>
              <div className="my-3 space-y-2">
                {build.files?.map((f) => (
                  <details key={f.path}>
                    <summary className="cursor-pointer break-all font-mono text-xs text-primary">
                      {f.path}
                    </summary>
                    <pre className="max-h-64 overflow-auto bg-background p-3 text-xs">
                      {f.content}
                    </pre>
                  </details>
                ))}
              </div>
              <div className="flex gap-2">
                <Button
                  disabled={disabled}
                  onClick={() => {
                    if (window.confirm("Να γραφτούν τα αρχεία αυτού του σχεδίου;"))
                      void studio.resolvePlan(build.plan_id, true);
                  }}
                >
                  <Check className="size-4" />
                  Έγκριση
                </Button>
                <Button
                  variant="outline"
                  disabled={disabled}
                  onClick={() => void studio.resolvePlan(build.plan_id, false)}
                >
                  <X className="size-4" />
                  Απόρριψη
                </Button>
              </div>
            </details>
          ))}
        <div className="flex flex-wrap items-center gap-2 border-y border-border py-3">
          <select
            aria-label="Εφαρμογή"
            value={studio.selected}
            onChange={(e) => studio.setSelected(e.target.value)}
            disabled={disabled || !studio.apps.length}
            className="h-9 min-w-0 max-w-full rounded border border-input bg-background px-3 text-sm"
          >
            <option value="" disabled>
              Επιλογή εφαρμογής
            </option>
            {studio.apps.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
          <span
            className={`mr-auto text-xs ${studio.running ? "text-ok" : "text-muted-foreground"}`}
          >
            {studio.running ? "Σε εκτέλεση" : "Σταματημένη"}
          </span>
          <Button
            variant="outline"
            disabled={disabled || !app || studio.running}
            onClick={() => void studio.run()}
          >
            <Play className="size-4" />
            Run
          </Button>
          <Button
            variant="outline"
            disabled={disabled || !studio.running}
            onClick={() => void studio.stop()}
          >
            <Square className="size-4" />
            Stop
          </Button>
          <Button
            variant="outline"
            size="icon"
            aria-label="Λήψη εφαρμογής"
            title="Download ZIP"
            disabled={disabled || !app}
            onClick={() => void studio.download()}
          >
            <Download className="size-4" />
          </Button>
        </div>
        {studio.approval && (
          <div
            role="status"
            className="flex flex-wrap items-center gap-3 border-l-2 border-warn pl-3 text-sm"
          >
            <p className="flex-1">
              Έγκριση εκτέλεσης: <strong>{studio.selected}</strong>
            </p>
            <Button disabled={disabled} onClick={() => void studio.resolveRun(true)}>
              Έγκριση Run
            </Button>
            <Button
              variant="outline"
              disabled={disabled}
              onClick={() => void studio.resolveRun(false)}
            >
              Απόρριψη Run
            </Button>
          </div>
        )}
        {!studio.apps.length && !studio.loading && (
          <p className="py-8 text-sm text-muted-foreground">Δεν υπάρχουν παραγόμενες εφαρμογές.</p>
        )}
        {app && (
          <div className="grid min-w-0 gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
            <aside className="min-w-0 space-y-3 lg:border-r lg:border-border lg:pr-4">
              <h2 className="flex items-center justify-between text-xs font-semibold">
                FILES <span className="text-muted-foreground">{app.file_count}</span>
              </h2>
              <Input
                aria-label="Αναζήτηση αρχείων"
                placeholder="Αναζήτηση αρχείων"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
              <div className="max-h-96 overflow-auto">
                <StudioFiles
                  files={app.files.filter((f) =>
                    f.name.toLowerCase().includes(filter.toLowerCase()),
                  )}
                  selected={studio.file}
                  onSelect={(path) => void studio.selectFile(path)}
                />
              </div>
            </aside>
            <div className="min-w-0">
              <Tabs value={tab} onValueChange={setTab}>
                <TabsList className="flex h-auto flex-wrap justify-start">
                  <TabsTrigger value="code">
                    <FileCode2 className="size-3" />
                    Code
                  </TabsTrigger>
                  <TabsTrigger value="tests">
                    <FlaskConical className="size-3" />
                    Tests
                  </TabsTrigger>
                  <TabsTrigger value="repair">
                    <Wrench className="size-3" />
                    Repair
                  </TabsTrigger>
                  <TabsTrigger value="logs">
                    <Terminal className="size-3" />
                    Logs
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="code">
                  <p className="mb-2 break-all font-mono text-xs text-primary">
                    {studio.file || "Επιλογή αρχείου"}
                  </p>
                  <pre
                    aria-label="Πηγαίος κώδικας"
                    className="h-96 overflow-auto border border-border bg-background p-4 font-mono text-xs leading-6"
                  >
                    {studio.code}
                  </pre>
                </TabsContent>
                <TabsContent value="tests" className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Button disabled={disabled} onClick={() => void studio.test()}>
                      <FlaskConical className="size-4" />
                      Εκτέλεση tests
                    </Button>
                    {studio.busy === "tests" && (
                      <Button variant="outline" onClick={studio.cancel}>
                        <Square className="size-4" />
                        Διακοπή
                      </Button>
                    )}
                    <span
                      role="status"
                      className={`text-xs ${studio.result?.ok ? "text-ok" : "text-warn"}`}
                    >
                      {studio.busy === "tests"
                        ? "Εκτελείται…"
                        : studio.result
                          ? `${studio.result.status} · ${studio.result.duration_seconds ?? "—"}s`
                          : "Δεν έχει εκτελεστεί"}
                    </span>
                  </div>
                  <pre
                    aria-label="Κονσόλα tests"
                    role="log"
                    aria-live="polite"
                    className="h-80 overflow-auto border border-border bg-background p-4 font-mono text-xs"
                  >
                    {studio.consoleText || studio.result?.error || ""}
                  </pre>
                </TabsContent>
                <TabsContent value="repair" className="space-y-4">
                  <Button
                    disabled={disabled}
                    onClick={() => {
                      if (
                        window.confirm(
                          "Να εκτελεστούν tests και να σταλούν επιλεγμένα αρχεία στο AI για διάγνωση; Δεν εφαρμόζονται αλλαγές.",
                        )
                      )
                        void studio.diagnose();
                    }}
                  >
                    <Wrench className="size-4" />
                    Διάγνωση αποτυχίας
                  </Button>
                  <div className="flex flex-wrap gap-2">
                    {studio.repairs
                      .filter((p) => p.status === "pending_review")
                      .map((p) => (
                        <Button
                          variant="outline"
                          key={p.repair_id}
                          disabled={disabled}
                          onClick={() => void studio.openRepair(p.repair_id)}
                        >
                          {p.summary.slice(0, 60) || p.repair_id}
                        </Button>
                      ))}
                  </div>
                  {studio.repair ? (
                    <StudioRepair
                      detail={studio.repair}
                      busy={disabled}
                      onResolve={(approve) => void studio.resolveRepair(approve)}
                    />
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Δεν έχει επιλεγεί πρόταση επισκευής.
                    </p>
                  )}
                </TabsContent>
                <TabsContent value="logs">
                  <pre
                    aria-label="Logs εφαρμογής"
                    role="log"
                    className="h-96 overflow-auto border border-border bg-background p-4 font-mono text-xs"
                  >
                    {studio.logs || "Δεν υπάρχουν logs."}
                  </pre>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
        {studio.busy && (
          <p role="status" className="flex items-center gap-2 text-xs text-primary">
            <Loader2 className="size-3 animate-spin motion-reduce:animate-none" />
            {studio.busy}
          </p>
        )}
      </div>
    </div>
  );
}
