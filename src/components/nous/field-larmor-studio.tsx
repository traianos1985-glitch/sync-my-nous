import { useRef, useState } from "react";
import {
  Compass,
  FlaskConical,
  Send,
  Save,
  RefreshCw,
  Download,
  MapPin,
  Square,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useDashboardRequests } from "./use-dashboard-requests";
import {
  fieldConversation,
  fieldCoordinates,
  requireFieldSuccess,
  toTesla,
  type FieldContext,
  type FieldEntry,
  type FieldMaterial,
  type FieldTurn,
  type FieldUnit,
  type LarmorResult,
} from "./field-larmor-model";

export function FieldLarmorStudio({
  connected,
  mode,
}: {
  connected: boolean;
  mode: "field" | "larmor";
}) {
  const request = useDashboardRequests();
  const [context, setContext] = useState<FieldContext>({
    site: "",
    terrain: "",
    equipment: "",
    observations: "",
  });
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<FieldTurn[]>([]);
  const [result, setResult] = useState<LarmorResult | null>(null);
  const [materials, setMaterials] = useState<Record<string, FieldMaterial>>({});
  const [material, setMaterial] = useState("cu");
  const [field, setField] = useState("48.23");
  const [unit, setUnit] = useState<FieldUnit>("µT");
  const [harmonic, setHarmonic] = useState(1);
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [entries, setEntries] = useState<FieldEntry[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const active = useRef<AbortController | null>(null);
  const lock = useRef(false);
  function patch(key: keyof FieldContext, value: string) {
    setContext((previous) => ({ ...previous, [key]: value }));
  }
  async function run(label: string, operation: (signal: AbortSignal) => Promise<void>) {
    if (lock.current || !connected) return;
    lock.current = true;
    const controller = new AbortController();
    active.current = controller;
    setBusy(label);
    setError("");
    setNotice("");
    try {
      await operation(controller.signal);
    } catch (failure) {
      if (!controller.signal.aborted)
        setError(failure instanceof Error ? failure.message : "Αποτυχία επικοινωνίας με NOUS.");
    } finally {
      lock.current = false;
      active.current = null;
      setBusy(null);
    }
  }
  async function send() {
    await run("Συνομιλία", async (signal) => {
      const conversation = fieldConversation(history, context, question, result);
      const response = requireFieldSuccess(
        await request<{ reply: string; error?: string }>("/larmor/chat", {
          method: "POST",
          body: JSON.stringify({ conversation }),
          signal,
        }),
      );
      if (
        !response.reply?.trim() ||
        /^(Σφάλμα|Error|Provider request failed)/i.test(response.reply)
      )
        throw new Error(response.reply || "Κενή απάντηση NOUS.");
      signal.throwIfAborted();
      // Keep the actual context sent to NOUS for accurate exports and follow-up.
      setHistory([...conversation, { role: "assistant", content: response.reply }]);
      setQuestion("");
    });
  }
  async function calculate() {
    await run("Υπολογισμός", async (signal) => {
      const b_field_T = toTesla(field, unit);
      const data = requireFieldSuccess(
        await request<LarmorResult & { error?: string }>("/larmor/calculate", {
          method: "POST",
          body: JSON.stringify({ material, b_field_T }),
          signal,
        }),
      );
      if (!Number.isFinite(data.f_larmor_hz) || data.f_larmor_hz <= 0)
        throw new Error("Μη έγκυρος υπολογισμός από NOUS.");
      signal.throwIfAborted();
      setResult(data);
      setHarmonic(1);
    });
  }
  function download() {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            context,
            coordinates: fieldCoordinates(lat, lon),
            calculation: result,
            conversation: history,
            exported_at: new Date().toISOString(),
            classification: "observations_not_verified_detection",
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "nous-field-session.json";
    link.click();
    URL.revokeObjectURL(url);
  }
  const inputStyle = "mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";
  return (
    <div className="min-w-0 flex-1 overflow-y-auto p-4 md:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
          <div>
            <div className="flex items-center gap-2 text-primary">
              <Compass className="size-5" />
              <span className="font-mono text-xs">NOUS / FIELD RESEARCH</span>
            </div>
            <h1 className="mt-2 font-display text-2xl font-semibold">
              {mode === "field" ? "Interactive Field Assistant" : "Larmor Studio"}
            </h1>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              try {
                download();
              } catch (failure) {
                setError(String(failure));
              }
            }}
          >
            <Download className="mr-2 size-4" />
            Εξαγωγή συνεδρίας
          </Button>
        </header>
        <p className="border-l-2 border-warn pl-3 text-sm text-muted-foreground">
          Η ραβδοσκοπία δεν αποτελεί επιστημονικά επιβεβαιωμένη μέθοδο εντοπισμού. Οι συχνότητες
          Larmor είναι υπολογισμοί αναφοράς, όχι απόδειξη υλικού, βάθους ή θέσης.
        </p>
        {!connected && (
          <p role="status" className="text-sm text-warn">
            Σύνδεσε το NOUS από τις Ρυθμίσεις για συνομιλία, υπολογισμό και ημερολόγιο.
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="text-sm text-ok">
            {notice}
          </p>
        )}
        <div className="grid gap-8 lg:grid-cols-[1fr_1.3fr]">
          <section className="min-w-0 space-y-4">
            <h2 className="flex items-center gap-2 font-semibold">
              <MapPin className="size-4 text-primary" />
              Συνθήκες πεδίου
            </h2>
            <label className="block text-sm">
              Περιοχή / τίτλος
              <Input
                value={context.site}
                maxLength={120}
                onChange={(event) => patch("site", event.target.value)}
                className="mt-1"
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm">
                Έδαφος
                <Input
                  value={context.terrain}
                  maxLength={180}
                  onChange={(event) => patch("terrain", event.target.value)}
                  className="mt-1"
                />
              </label>
              <label className="block text-sm">
                Εξοπλισμός
                <Input
                  value={context.equipment}
                  maxLength={180}
                  onChange={(event) => patch("equipment", event.target.value)}
                  className="mt-1"
                />
              </label>
            </div>
            <label className="block text-sm">
              Παρατηρήσεις / μετρήσεις
              <Textarea
                value={context.observations}
                maxLength={2000}
                onChange={(event) => patch("observations", event.target.value)}
                rows={5}
                className="mt-1"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm">
                Γεωγραφικό πλάτος
                <Input
                  value={lat}
                  inputMode="decimal"
                  onChange={(event) => setLat(event.target.value)}
                  className="mt-1"
                />
              </label>
              <label className="text-sm">
                Γεωγραφικό μήκος
                <Input
                  value={lon}
                  inputMode="decimal"
                  onChange={(event) => setLon(event.target.value)}
                  className="mt-1"
                />
              </label>
            </div>
            <div className="border-t border-border pt-4">
              <h2 className="flex items-center gap-2 font-semibold">
                <FlaskConical className="size-4 text-signal" />
                Υπολογισμός Larmor
              </h2>
              <div className="mt-3 flex flex-wrap items-end gap-3">
                <label className="min-w-0 flex-1 text-sm">
                  Ισότοπο / υλικό
                  <select
                    aria-label="Ισότοπο / υλικό"
                    value={material}
                    onChange={(event) => setMaterial(event.target.value)}
                    className={inputStyle}
                  >
                    {Object.keys(materials).length ? (
                      Object.entries(materials).map(([key, item]) => (
                        <option key={key} value={key}>
                          {item.name}
                        </option>
                      ))
                    ) : (
                      <option value="cu">⁶³Cu — χαλκός</option>
                    )}
                  </select>
                </label>
                <Button
                  variant="outline"
                  disabled={!connected || !!busy}
                  title="Φόρτωση υλικών NOUS"
                  aria-label="Φόρτωση υλικών NOUS"
                  onClick={() =>
                    void run("Υλικά", async (signal) => {
                      const data = requireFieldSuccess(
                        await request<Record<string, FieldMaterial> & { error?: string }>(
                          "/larmor/materials",
                          { signal },
                        ),
                      );
                      signal.throwIfAborted();
                      setMaterials(data);
                    })
                  }
                >
                  <RefreshCw className="size-4" />
                </Button>
              </div>
              <div className="mt-3 grid grid-cols-[1fr_80px] gap-3">
                <label className="text-sm">
                  Μαγνητικό πεδίο B
                  <Input
                    value={field}
                    type="number"
                    step="any"
                    min="0"
                    onChange={(event) => {
                      setField(event.target.value);
                      setResult(null);
                    }}
                    className="mt-1"
                  />
                </label>
                <label className="text-sm">
                  Μονάδα
                  <select
                    value={unit}
                    onChange={(event) => {
                      setUnit(event.target.value as FieldUnit);
                      setResult(null);
                    }}
                    className={inputStyle}
                  >
                    {["µT", "mT", "T"].map((item) => (
                      <option key={item}>{item}</option>
                    ))}
                  </select>
                </label>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                48,23 µT = 0,00004823 T. Η αρχική τιμή είναι παράδειγμα, όχι επιτόπια μέτρηση.
              </p>
              <Button
                className="mt-3"
                disabled={!connected || !!busy}
                onClick={() => void calculate()}
              >
                <FlaskConical className="mr-2 size-4" />
                Υπολογισμός
              </Button>
              {result && (
                <div className="mt-4 space-y-3 border-l-2 border-signal pl-3">
                  <p className="text-sm">
                    {result.material} · B = {result.b_field_T.toPrecision(6)} T
                  </p>
                  <p className="font-mono text-2xl text-signal">
                    {result.f_larmor_hz.toFixed(3)} Hz
                  </p>
                  <label className="block text-sm">
                    Αρμονική n: {harmonic}
                    <input
                      aria-label="Αρμονική n"
                      className="mt-2 w-full accent-current"
                      type="range"
                      min={1}
                      max={50}
                      value={harmonic}
                      onChange={(event) => setHarmonic(Number(event.target.value))}
                    />
                  </label>
                  <p className="font-mono text-sm">
                    n × fL = {(result.f_larmor_hz * harmonic).toFixed(3)} Hz
                  </p>
                  <svg
                    viewBox="0 0 320 70"
                    role="img"
                    aria-label="Συχνότητες αρμονικών Larmor από 1 έως 50"
                    className="h-20 w-full text-signal"
                  >
                    <path d="M0 65H320" stroke="currentColor" opacity="0.3" />
                    {[1, 10, 20, 30, 40, 50].map((n) => (
                      <g key={n}>
                        <path d={`M${n * 6} 65V${65 - n}`} stroke="currentColor" strokeWidth="3" />
                        <text x={n * 6} y="12" fill="currentColor" fontSize="9" textAnchor="middle">
                          {n}
                        </text>
                      </g>
                    ))}
                  </svg>
                  <p className="text-xs text-muted-foreground">
                    fL = (γ/2π) × B · γ/2π = {result.gamma_hz_per_T} Hz/T. Τιμές κράματος:
                    πειραματικές, όχι γυρομαγνητική σταθερά ενιαίου ισοτόπου.
                  </p>
                </div>
              )}
            </div>
          </section>
          <section className="min-w-0 space-y-4">
            <h2 className="font-semibold">Συζήτηση με NOUS</h2>
            <div className="flex flex-wrap gap-2">
              {[
                "Πρότεινε ασφαλή επόμενα βήματα",
                "Σχεδίασε τυφλή δοκιμή με σημεία ελέγχου",
                "Έλεγξε πιθανές παρεμβολές",
              ].map((prompt) => (
                <Button
                  key={prompt}
                  variant="outline"
                  size="sm"
                  disabled={!!busy}
                  className="h-auto whitespace-normal text-left"
                  onClick={() => setQuestion(prompt)}
                >
                  {prompt}
                </Button>
              ))}
            </div>
            <div
              role="log"
              aria-label="Συνομιλία πεδίου"
              className="max-h-[480px] min-h-40 space-y-4 overflow-y-auto border-y border-border py-4"
            >
              {history.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Δεν υπάρχουν μηνύματα σε αυτή τη συνεδρία.
                </p>
              ) : (
                history.map((turn, index) => (
                  <article key={index} className="min-w-0">
                    <p
                      className={`text-xs font-semibold ${turn.role === "assistant" ? "text-primary" : "text-muted-foreground"}`}
                    >
                      {turn.role === "assistant"
                        ? "NOUS · AI ερμηνεία"
                        : "Ερευνητής · πλαίσιο & ερώτηση"}
                    </p>
                    <p className="mt-1 whitespace-pre-wrap break-words text-sm leading-6">
                      {turn.content}
                    </p>
                  </article>
                ))
              )}
            </div>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void send();
              }}
            >
              <label className="block text-sm">
                Ερώτηση πεδίου
                <Textarea
                  value={question}
                  maxLength={1000}
                  rows={3}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="mt-1"
                />
              </label>
              <div className="mt-3 flex gap-2">
                <Button type="submit" disabled={!connected || !!busy || !question.trim()}>
                  <Send className="mr-2 size-4" />
                  {busy === "Συνομιλία" ? "Απάντηση…" : "Αποστολή"}
                </Button>
                {busy ? (
                  <Button type="button" variant="outline" onClick={() => active.current?.abort()}>
                    <Square className="mr-2 size-4" />
                    Ακύρωση
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="ghost"
                    title="Νέα συνομιλία"
                    aria-label="Νέα συνομιλία"
                    onClick={() => setHistory([])}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                )}
              </div>
            </form>
            <p className="border-l-2 border-destructive pl-3 text-xs leading-5 text-muted-foreground">
              Πιθανά πυρομαχικά: μην πλησιάζεις, αγγίζεις ή σκάβεις· απομακρύνσου και ειδοποίησε το
              112. Για έρευνα σε ξένη ιδιοκτησία ή αρχαιολογικό χώρο απαιτούνται οι νόμιμες άδειες.
            </p>
            <fieldset className="space-y-2 border-t border-border pt-4">
              <legend className="font-semibold">Έλεγχοι πριν την έρευνα</legend>
              {[
                "Άδεια πρόσβασης και νόμιμη έρευνα",
                "Γνωστό σημείο ελέγχου και κενό δείγμα",
                "Επαναληπτική σάρωση σε κάθετες κατευθύνσεις",
                "Ανεξάρτητη επιβεβαίωση με κατάλληλο όργανο",
              ].map((item) => (
                <label key={item} className="flex items-start gap-2 text-sm">
                  <input type="checkbox" className="mt-1" />
                  {item}
                </label>
              ))}
            </fieldset>
          </section>
        </div>
        <section className="border-t border-border pt-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-semibold">Ημερολόγιο παρατηρήσεων</h2>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={!connected || !!busy}
                onClick={() =>
                  void run("Ημερολόγιο", async (signal) => {
                    const data = requireFieldSuccess(
                      await request<{ ok: boolean; entries: FieldEntry[]; error?: string }>(
                        "/field/list?limit=20",
                        { signal },
                      ),
                    );
                    signal.throwIfAborted();
                    setEntries(data.entries);
                  })
                }
              >
                <RefreshCw className="mr-2 size-4" />
                Ανανέωση
              </Button>
              <Button
                disabled={!connected || !!busy || !context.site.trim()}
                onClick={() =>
                  void run("Αποθήκευση", async (signal) => {
                    const coordinates = fieldCoordinates(lat, lon);
                    const data = requireFieldSuccess(
                      await request<{ ok: boolean; entry: FieldEntry; error?: string }>(
                        "/field/add",
                        {
                          method: "POST",
                          signal,
                          body: JSON.stringify({
                            title: context.site,
                            note: JSON.stringify(context),
                            ...coordinates,
                            entry_type: "note",
                            tags: ["field-assistant", "unverified"],
                            analysis:
                              [...history].reverse().find((turn) => turn.role === "assistant")
                                ?.content || "",
                          }),
                        },
                      ),
                    );
                    signal.throwIfAborted();
                    setEntries((previous) => [
                      data.entry,
                      ...previous.filter((entry) => entry.id !== data.entry.id),
                    ]);
                    setNotice("Η παρατήρηση αποθηκεύτηκε στο ημερολόγιο NOUS.");
                  })
                }
              >
                <Save className="mr-2 size-4" />
                Αποθήκευση
              </Button>
            </div>
          </div>
          {entries.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">Δεν έχουν φορτωθεί καταχωρήσεις.</p>
          ) : (
            <ul className="mt-4 divide-y divide-border">
              {entries.map((entry) => (
                <li key={entry.id} className="min-w-0 py-3">
                  <details>
                    <summary className="cursor-pointer break-words text-sm font-semibold">
                      {entry.title}{" "}
                      <span className="font-normal text-muted-foreground">
                        · {entry.timestamp.slice(0, 10)}
                      </span>
                    </summary>
                    <p className="mt-2 whitespace-pre-wrap break-words text-xs">{entry.note}</p>
                    {entry.lat != null && entry.lon != null && (
                      <p className="mt-2 font-mono text-xs">
                        GPS: {entry.lat}, {entry.lon}
                      </p>
                    )}
                    <p className="mt-2 whitespace-pre-wrap break-words text-sm">{entry.analysis}</p>
                  </details>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
