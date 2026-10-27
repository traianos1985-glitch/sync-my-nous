import { clearNousToken, getNousToken, setNousToken } from "@/lib/nous-api";
import { Button } from "@/components/ui/button";
import type { useDashboard } from "./use-dashboard";
export function ConnectionSettings({ dashboard }: { dashboard: ReturnType<typeof useDashboard> }) {
  const {
    tokenDraft,
    setTokenDraft,
    hasToken,
    setHasToken,
    hasSessionToken,
    setHasSessionToken,
    geminiTestState,
    setGeminiTestState,
    geminiTestMessage,
    setGeminiTestMessage,
    loadSystemStatus,
    testGeminiConnection,
  } = dashboard;
  return (
    <form
      className="mb-3 flex flex-col gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (!tokenDraft.trim()) return;
        try {
          setNousToken(tokenDraft);
          setTokenDraft("");
          setHasToken(true);
          setHasSessionToken(true);
          setGeminiTestState("idle");
          setGeminiTestMessage("");
          void loadSystemStatus();
        } catch (error) {
          setGeminiTestState("error");
          setGeminiTestMessage(error instanceof Error ? error.message : "Μη έγκυρο NOUS token.");
        }
      }}
    >
      <label htmlFor="nous-token" className="text-xs text-muted-foreground">
        NOUS API token{" "}
        {hasToken ? (
          <span className="text-primary">
            {hasSessionToken
              ? "· αποθηκευμένο σε αυτόν τον browser"
              : "· ρυθμισμένο από το περιβάλλον"}
          </span>
        ) : (
          <span className="text-warn">· δεν έχει οριστεί</span>
        )}
      </label>
      <div className="flex min-w-0 flex-wrap gap-2">
        <input
          id="nous-token"
          type="password"
          autoComplete="off"
          value={tokenDraft}
          onChange={(event) => setTokenDraft(event.target.value)}
          placeholder={hasToken ? "Νέο token για αντικατάσταση" : "Επικόλλησε το token"}
          className="w-full min-w-0 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-violet sm:w-auto sm:flex-1"
        />
        <Button
          type="submit"
          disabled={!tokenDraft.trim()}
          className="shrink-0 rounded-lg bg-primary px-3 text-sm font-semibold text-primary-foreground disabled:opacity-50"
        >
          Αποθήκευση
        </Button>
        {hasSessionToken && (
          <Button
            variant="outline"
            type="button"
            onClick={() => {
              clearNousToken();
              setHasToken(Boolean(getNousToken()));
              setHasSessionToken(false);
              setGeminiTestState("idle");
              setGeminiTestMessage("");
              void loadSystemStatus();
            }}
            className="shrink-0 rounded-lg border border-border px-3 text-sm text-muted-foreground"
          >
            Αφαίρεση
          </Button>
        )}
      </div>
      <p className="text-[11px] text-muted-foreground">
        Το token αποθηκεύεται μόνο σε αυτόν τον browser μέχρι να το αφαιρέσεις.
      </p>
      <Button
        variant="outline"
        type="button"
        onClick={() => void testGeminiConnection()}
        disabled={!hasToken || geminiTestState === "testing"}
        className="self-start rounded-lg border border-primary/40 px-3 py-2 text-xs font-semibold text-primary disabled:opacity-50"
      >
        {geminiTestState === "testing" ? "Έλεγχος Gemini…" : "Έλεγχος επικοινωνίας με Gemini"}
      </Button>
      {geminiTestMessage && (
        <p className={`text-xs ${geminiTestState === "ok" ? "text-ok" : "text-warn"}`}>
          {geminiTestMessage}
        </p>
      )}
    </form>
  );
}
