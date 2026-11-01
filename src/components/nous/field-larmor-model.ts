export type FieldContext = {
  site: string;
  terrain: string;
  equipment: string;
  observations: string;
};
export type FieldTurn = { role: "user" | "assistant"; content: string };
export type FieldEntry = {
  id: string;
  title: string;
  note: string;
  analysis: string;
  timestamp: string;
  lat: number | null;
  lon: number | null;
};
export type LarmorResult = {
  material: string;
  material_key: string;
  b_field_T: number;
  gamma_hz_per_T: number;
  f_larmor_hz: number;
  harmonics: { n: number; hz: number }[];
};
export type FieldMaterial = { name: string; gamma: number; notes: string };
export type FieldUnit = "µT" | "mT" | "T";
export function toTesla(value: string, unit: FieldUnit): number {
  if (!value.trim()) throw new Error("Συμπλήρωσε το μαγνητικό πεδίο.");
  const numeric = Number(value);
  const result = numeric * (unit === "µT" ? 1e-6 : unit === "mT" ? 1e-3 : 1);
  if (!Number.isFinite(result) || result <= 0)
    throw new Error("Το πεδίο πρέπει να είναι θετικός, πεπερασμένος αριθμός.");
  return result;
}
export function fieldCoordinates(
  lat: string,
  lon: string,
): { lat: number | null; lon: number | null } {
  if (!lat.trim() && !lon.trim()) return { lat: null, lon: null };
  const latitude = Number(lat),
    longitude = Number(lon);
  if (
    !lat.trim() ||
    !lon.trim() ||
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    Math.abs(latitude) > 90 ||
    Math.abs(longitude) > 180
  )
    throw new Error("Δώσε έγκυρο ζεύγος συντεταγμένων (-90…90, -180…180).");
  return { lat: latitude, lon: longitude };
}
export function fieldConversation(
  history: FieldTurn[],
  context: FieldContext,
  question: string,
  result: LarmorResult | null,
): FieldTurn[] {
  const content = `Βοήθεια πεδίου. Διαχώρισε παρατήρηση, υπόθεση και μέτρηση. Μην θεωρείς τη ραβδοσκοπία επιβεβαιωμένη ανίχνευση. Πρότεινε ασφαλή, μη επεμβατικά βήματα και τυφλό έλεγχο.\nΠεριοχή: ${context.site}\nΈδαφος: ${context.terrain}\nΕξοπλισμός: ${context.equipment}\nΠαρατηρήσεις: ${context.observations}\n${result ? `Υπολογισμός αναφοράς: ${JSON.stringify({ material: result.material, b_field_T: result.b_field_T, f_larmor_hz: result.f_larmor_hz })}\n` : ""}Ερώτηση: ${question.trim()}`;
  if (!question.trim()) throw new Error("Γράψε την ερώτησή σου.");
  if (content.length > 4000)
    throw new Error("Μείωσε την ερώτηση ή τις παρατηρήσεις (όριο 4.000 χαρακτήρων μαζί).");
  const retained = history
    .slice(-18)
    .map((turn) => ({ ...turn, content: turn.content.slice(0, 4000) }));
  while (retained.reduce((sum, turn) => sum + turn.content.length, content.length) > 16000)
    retained.shift();
  // Never begin a trimmed conversation with an orphan assistant reply.
  while (retained[0]?.role === "assistant") retained.shift();
  return [...retained, { role: "user", content }];
}
export function requireFieldSuccess<T extends { ok?: boolean; error?: string }>(response: T): T {
  if (response.ok === false || response.error)
    throw new Error(response.error || "Το NOUS δεν ολοκλήρωσε την ενέργεια.");
  return response;
}
