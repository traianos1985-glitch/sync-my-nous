import { nousStream, type NousApiOptions } from "./nous-api";
import type { ValidationResult } from "../components/nous/app-studio-model";

export async function runStudioValidation(appName: string, onOutput: (text: string) => void, options: NousApiOptions = {}): Promise<ValidationResult> {
  const response = await nousStream("/remote/app-builder/test-stream", {
    ...options, method: "POST", body: JSON.stringify({ app_name: appName, timeout_seconds: 120 }), timeoutMs: 75_000,
  });
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Η κονσόλα δεν είναι διαθέσιμη.");
  const abort = () => { void reader.cancel(); };
  options.signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(abort, 150_000);
  let pending = "";
  let result: ValidationResult | undefined;
  const decoder = new TextDecoder();
  try {
    options.signal?.throwIfAborted();
    while (true) {
      const { value, done } = await reader.read();
      pending += decoder.decode(value, { stream: !done });
      if (pending.length > 1_000_000) throw new Error("Υπερβολικά μεγάλο αποτέλεσμα runner.");
      let match: RegExpExecArray | null;
      while ((match = /\r?\n\r?\n/.exec(pending))) {
        const frame = pending.slice(0, match.index);
        pending = pending.slice(match.index + match[0].length);
        const event = frame.split(/\r?\n/).find((line) => line.startsWith("event:"))?.slice(6).trim();
        const data = frame.split(/\r?\n/).filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).join("\n");
        if (!data) continue;
        const parsed = JSON.parse(data);
        if (event === "output" && typeof parsed.text === "string") onOutput(parsed.text);
        if (event === "result" && typeof parsed.ok === "boolean" && typeof parsed.status === "string") result = parsed;
      }
      if (done || result) break;
    }
    options.signal?.throwIfAborted();
    if (!result) throw new Error("Η σύνδεση διακόπηκε· η εκτέλεση δεν επιβεβαιώθηκε. Δεν έγινε αυτόματη επανάληψη.");
    return result;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", abort);
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}