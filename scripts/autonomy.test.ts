import { describe, expect, test } from "bun:test";
import {
  DEFAULT_INTERVAL_SECONDS,
  filterAutonomyEvents,
  formatElapsedSeconds,
  formatEventBadge,
  formatEventTimestamp,
  getWatchdogTone,
  isEmergencyStopped,
  validateInterval,
  type AutonomyEventItem,
  type AutonomyServiceState,
  type WatchdogStatus,
} from "../src/components/nous/autonomy-model";

describe("autonomy service model", () => {
  test("validates interval ranges and defaults gracefully", () => {
    expect(validateInterval(300)).toEqual({ valid: true, value: 300 });
    expect(validateInterval("60")).toEqual({ valid: true, value: 60 });

    const tooLow = validateInterval(2);
    expect(tooLow.valid).toBe(false);
    expect(tooLow.error).toContain("ελάχιστο");

    const tooHigh = validateInterval(999999);
    expect(tooHigh.valid).toBe(false);
    expect(tooHigh.error).toContain("μέγιστο");

    const invalid = validateInterval("not-a-number");
    expect(invalid.valid).toBe(false);
    expect(invalid.value).toBe(DEFAULT_INTERVAL_SECONDS);
  });

  test("formats elapsed seconds accurately into natural strings", () => {
    expect(formatElapsedSeconds(null)).toBe("ποτέ");
    expect(formatElapsedSeconds(-10)).toBe("ποτέ");
    expect(formatElapsedSeconds(0)).toBe("μόλις τώρα");
    expect(formatElapsedSeconds(42)).toBe("42δ πριν");
    expect(formatElapsedSeconds(125)).toBe("2λ πριν");
    expect(formatElapsedSeconds(3660)).toBe("1ω 1λ πριν");
  });

  test("formats timestamps safely", () => {
    expect(formatEventTimestamp(0)).toBe("—");
    const formatted = formatEventTimestamp(1700000000);
    expect(typeof formatted).toBe("string");
    expect(formatted.length).toBeGreaterThan(0);
  });

  test("assigns semantic tones and labels to autonomy events", () => {
    expect(formatEventBadge("service_cycle_ok")).toEqual({
      label: "Επιτυχής κύκλος",
      tone: "ok",
    });
    expect(formatEventBadge("service_cycle_error")).toEqual({
      label: "Σφάλμα κύκλου",
      tone: "destructive",
    });
    expect(formatEventBadge("emergency_stop")).toEqual({
      label: "Emergency Stop",
      tone: "destructive",
    });
    expect(formatEventBadge("service_enabled").tone).toBe("info");
    expect(formatEventBadge("service_disabled").tone).toBe("warn");
    expect(formatEventBadge("watchdog_warning").tone).toBe("warn");
    expect(formatEventBadge("service_skip").tone).toBe("muted");
    expect(formatEventBadge("custom_event").tone).toBe("muted");
  });

  test("identifies emergency stop state and watchdog tones", () => {
    expect(isEmergencyStopped(null)).toBe(false);
    expect(isEmergencyStopped({ emergency_stop: false } as unknown as AutonomyServiceState)).toBe(
      false,
    );
    expect(isEmergencyStopped({ emergency_stop: true } as unknown as AutonomyServiceState)).toBe(
      true,
    );

    expect(getWatchdogTone(null)).toBe("muted");
    expect(getWatchdogTone({ ok: true } as unknown as WatchdogStatus)).toBe("ok");
    expect(
      getWatchdogTone({ ok: false, action: "needs_attention" } as unknown as WatchdogStatus),
    ).toBe("warn");
    expect(
      getWatchdogTone({ ok: false, action: "needs_restart" } as unknown as WatchdogStatus),
    ).toBe("destructive");
  });

  test("filters autonomy events by category and search keyword", () => {
    const sampleEvents: AutonomyEventItem[] = [
      { time: 100, event: "service_cycle_ok", data: { step: "learning" } },
      { time: 101, event: "service_cycle_error", data: { error: "NetworkTimeout" } },
      { time: 102, event: "emergency_stop", data: { reason: "manual_kill_switch" } },
      { time: 103, event: "service_enabled", data: { interval: 60 } },
      { time: 104, event: "service_disabled", data: {} },
      { time: 105, event: "service_skip", data: { reason: "disabled" } },
    ];

    expect(filterAutonomyEvents(sampleEvents, "all", "")).toHaveLength(6);
    expect(filterAutonomyEvents(sampleEvents, "errors", "")).toHaveLength(2);
    expect(filterAutonomyEvents(sampleEvents, "cycles", "")).toHaveLength(2);
    expect(filterAutonomyEvents(sampleEvents, "lifecycle", "")).toHaveLength(3);

    const searched = filterAutonomyEvents(sampleEvents, "all", "kill_switch");
    expect(searched).toHaveLength(1);
    expect(searched[0].event).toBe("emergency_stop");

    const searchError = filterAutonomyEvents(sampleEvents, "all", "network");
    expect(searchError).toHaveLength(1);
    expect(searchError[0].event).toBe("service_cycle_error");
  });
});
