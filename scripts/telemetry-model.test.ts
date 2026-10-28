import { describe, expect, it } from "bun:test";
import {
  appendResourcePoint,
  buildMissionDistribution,
  calculateResourceTone,
  formatUptime,
} from "../src/components/nous/telemetry-model";

describe("telemetry model", () => {
  it("formats uptime and handles missing values", () => {
    expect(formatUptime(0)).toBe("0λ 0δ");
    expect(formatUptime(3665)).toBe("1ω 1λ");
    expect(formatUptime()).toBe("—");
    expect(formatUptime(-1)).toBe("—");
  });

  it("classifies resource pressure conservatively", () => {
    expect(calculateResourceTone()).toBe("ok");
    expect(calculateResourceTone(69.9)).toBe("ok");
    expect(calculateResourceTone(70)).toBe("warn");
    expect(calculateResourceTone(85)).toBe("destructive");
  });

  it("builds non-negative mission distribution values", () => {
    expect(
      buildMissionDistribution({ active: 2, awaiting: 1, failed: -1 }).map((item) => item.count),
    ).toEqual([2, 1, 0]);
  });

  it("keeps only the latest resource history points", () => {
    const points = Array.from({ length: 14 }, (_, index) => ({
      time: String(index),
      cpu: index,
      memory: index + 1,
    }));
    const history = points.slice(0, 11);
    const result = appendResourcePoint(history, points[11], 12);
    expect(result).toHaveLength(12);
    expect(result[0].time).toBe("0");
    const capped = appendResourcePoint(result, points[12], 12);
    expect(capped).toHaveLength(12);
    expect(capped[0].time).toBe("1");
    expect(capped[11].time).toBe("12");
  });
});
