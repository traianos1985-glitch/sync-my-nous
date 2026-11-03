import { describe, expect, test } from "bun:test";
import { buildSwarmView, validateMission } from "../src/components/nous/swarm-model";
import {
  canSendCompanionCommand,
  companionSetupSteps,
  validateTap,
} from "../src/components/nous/companion-model";
import { describeTick, schedulerCycleUrl } from "../src/components/nous/scheduler-model";

const trace = {
  mission: "m",
  status: "completed",
  simulated: true,
  executed: false,
  trace: [
    {
      role: "architect",
      status: "planned",
      simulated: true,
      executed: false,
      plan: [
        { id: 1, role: "researcher", task: "r" },
        { id: 2, role: "coder", task: "c" },
        { id: 3, role: "reviewer", task: "v" },
      ],
    },
    { role: "researcher", status: "done", simulated: true, executed: false },
    { role: "coder", status: "done", simulated: true, executed: false },
    { role: "reviewer", status: "not_run", simulated: true, executed: false },
  ],
};

describe("swarm view", () => {
  test("maps architect to leader and plan steps to three workers", () => {
    const view = buildSwarmView(trace);
    expect(view.leader?.role).toBe("architect");
    expect(view.workers.map((w) => w.role)).toEqual(["researcher", "coder", "reviewer"]);
    expect(view.workers[2].status).toBe("not_run");
  });
  test("simulated agents never count as executed", () => {
    const view = buildSwarmView(trace);
    expect(view.simulated).toBe(true);
    expect(view.executedCount).toBe(0);
  });
  test("mission must be non-empty and at most 2000 characters", () => {
    expect(validateMission("   ")).not.toBeNull();
    expect(validateMission("x".repeat(2001))).not.toBeNull();
    expect(validateMission("x".repeat(2000))).toBeNull();
  });
});

describe("companion", () => {
  test("a pairing token alone does not enable commands off Android", () => {
    const status = { available: false, pairing_configured: true, host_android: false };
    expect(canSendCompanionCommand(status, true)).toBe(false);
    expect(companionSetupSteps(status).find((s) => s.id === "host")?.done).toBe(false);
  });
  test("commands need both backend availability and a NOUS token", () => {
    const status = { available: true, pairing_configured: true, host_android: true };
    expect(canSendCompanionCommand(status, true)).toBe(true);
    expect(canSendCompanionCommand(status, false)).toBe(false);
  });
  test("tap coordinates must be finite and between 0 and 10000", () => {
    expect(validateTap("100", "200")).toEqual({ x: 100, y: 200 });
    expect(validateTap("-1", "5")).toBeNull();
    expect(validateTap("", "5")).toBeNull();
    expect(validateTap("10001", "5")).toBeNull();
  });
});

describe("scheduler", () => {
  test("cycle url points at the Render service cycle endpoint", () => {
    expect(schedulerCycleUrl("https://nous-ai-os-api.onrender.com/")).toBe(
      "https://nous-ai-os-api.onrender.com/remote/service/cycle",
    );
  });
  test("not-due tick reports seconds until next cycle", () => {
    expect(describeTick({ ok: true, ran: false, reason: "not_due", next_due_in: 41.2 })).toContain(
      "42s",
    );
  });
});
