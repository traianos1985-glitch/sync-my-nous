export type CompanionStatus = {
  available: boolean;
  package?: string;
  receiver?: string;
  pairing_configured?: boolean;
  host_android?: boolean;
  missing?: string[];
  pairing_env?: string;
  commands?: string[];
};

export type CompanionStep = { id: string; label: string; done: boolean; hint: string };

export const COMPANION_PAIRING_ENV = "NOUS_COMPANION_PAIRING_TOKEN";

/** Setup checklist; each step is derived only from what the backend reports. */
export function companionSetupSteps(status: CompanionStatus | null): CompanionStep[] {
  const hostAndroid = status?.host_android === true;
  const paired = status?.pairing_configured === true;
  const env = status?.pairing_env ?? COMPANION_PAIRING_ENV;
  return [
    {
      id: "host",
      label: "Ο NOUS τρέχει πάνω στο κινητό Android",
      done: hostAndroid,
      hint: hostAndroid
        ? "Ο server βλέπει τις εντολές Android."
        : "Ο server στη Render δεν είναι κινητό. Οι εντολές δουλεύουν μόνο όταν ο NOUS τρέχει στο ίδιο το κινητό (Termux).",
    },
    {
      id: "apk",
      label: "Εγκατεστημένη εφαρμογή NOUS Companion",
      done: status?.available === true,
      hint: "Χτίσε την εφαρμογή από τον φάκελο android_companion, εγκατέστησέ την και ενεργοποίησε την Προσβασιμότητα.",
    },
    {
      id: "pairing",
      label: "Κωδικός σύζευξης",
      done: paired,
      hint: paired
        ? "Ο κωδικός σύζευξης έχει οριστεί."
        : `Όρισε τη μεταβλητή ${env} στον server που τρέχει πάνω στο κινητό, με την ίδια τιμή που βάζεις στην εφαρμογή.`,
    },
  ];
}

export function canSendCompanionCommand(status: CompanionStatus | null, connected: boolean) {
  return connected && status?.available === true;
}

export function validateTap(x: string, y: string): { x: number; y: number } | null {
  const nx = Number(x);
  const ny = Number(y);
  if (!x.trim() || !y.trim() || !Number.isFinite(nx) || !Number.isFinite(ny)) return null;
  if (nx < 0 || ny < 0 || nx > 10000 || ny > 10000) return null;
  return { x: nx, y: ny };
}
