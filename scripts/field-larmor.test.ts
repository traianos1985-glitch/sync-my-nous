import { describe, expect, it } from "bun:test";
import {
  fieldConversation,
  fieldCoordinates,
  requireFieldSuccess,
  toTesla,
} from "../src/components/nous/field-larmor-model";
const context = {
  site: "Test site",
  terrain: "clay",
  equipment: "magnetometer",
  observations: "repeat readings",
};
describe("Field assistant contracts", () => {
  it("converts Earth scale microtesla without a thousand-fold error", () => {
    expect(toTesla("48.23", "µT")).toBeCloseTo(0.00004823, 12);
    expect(toTesla("0.04823", "mT")).toBeCloseTo(0.00004823, 12);
    expect(toTesla("0.00004823", "T")).toBeCloseTo(0.00004823, 12);
    expect(11.3114e6 * toTesla("48.23", "µT")).toBeCloseTo(545.548822, 6);
  });
  it("rejects invalid magnetic field", () => {
    for (const value of ["", "0", "-1", "Infinity", "NaN"])
      expect(() => toTesla(value, "T")).toThrow();
  });
  it("validates paired coordinate ranges without inventing zero locations", () => {
    expect(fieldCoordinates("", "")).toEqual({ lat: null, lon: null });
    expect(fieldCoordinates("37", "22")).toEqual({ lat: 37, lon: 22 });
    for (const pair of [
      ["91", "22"],
      ["37", "181"],
      ["", "22"],
      ["37", "NaN"],
    ])
      expect(() => fieldCoordinates(pair[0], pair[1])).toThrow();
  });
  it("bounds conversation to backend limits and preserves current context", () => {
    const history = Array.from({ length: 30 }, (_, index) => ({
      role: index % 2 ? ("assistant" as const) : ("user" as const),
      content: "x".repeat(5000),
    }));
    const turns = fieldConversation(history, context, "What next?", null);
    expect(turns.length).toBeLessThanOrEqual(20);
    expect(turns.reduce((sum, turn) => sum + turn.content.length, 0)).toBeLessThanOrEqual(16000);
    expect(turns.every((turn) => turn.content.length <= 4000)).toBe(true);
    expect(turns[0].role).toBe("user");
    expect(turns.at(-1)?.content).toContain(context.site);
  });
  it("rejects oversized input instead of silently discarding observations", () => {
    expect(() =>
      fieldConversation([], { ...context, observations: "x".repeat(4000) }, "Question", null),
    ).toThrow();
  });
  it("does not mark HTTP 200 domain errors as completed saves", () => {
    expect(() => requireFieldSuccess({ ok: false, error: "write failed" })).toThrow("write failed");
    expect(requireFieldSuccess({ ok: true, entry: { id: "server-id" } }).entry.id).toBe(
      "server-id",
    );
  });
});
