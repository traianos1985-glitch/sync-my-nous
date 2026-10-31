import { describe, expect, it } from "bun:test";
import {
  canRunNextStep,
  describeRunNext,
  filterMissions,
  missionStatusMeta,
  normalizeMission,
  summarizeMissions,
} from "../src/components/nous/mission-status";
import { formatApprovalPayload } from "../src/components/nous/approval-model";

describe("mission status and filtering", () => {
  const sampleMissions = [
    { id: "m-1", title: "Σάρωση ασφαλείας δικτύου", status: "running" },
    { id: "m-2", title: "Ανάλυση αρχείων καταγραφής", status: "awaiting_approval" },
    { id: "m-3", title: "Ενημέρωση βιβλιοθηκών", status: "completed" },
    { id: "m-4", title: "Αποτυχία backup βάσης", status: "failed" },
    { id: "m-5", title: "Σχεδιασμός νέου agent", status: "planning" },
  ];

  it("summarizes mission counts by status", () => {
    const summary = summarizeMissions(sampleMissions);
    expect(summary.active).toBe(3); // running, awaiting_approval, planning
    expect(summary.awaiting).toBe(1);
    expect(summary.failed).toBe(1);
    expect(summary.completed).toBe(1);
  });

  it("filters missions by tab", () => {
    expect(filterMissions(sampleMissions, "all")).toHaveLength(5);
    expect(filterMissions(sampleMissions, "active")).toHaveLength(3);
    expect(filterMissions(sampleMissions, "awaiting")).toHaveLength(1);
    expect(filterMissions(sampleMissions, "failed")).toHaveLength(1);
    expect(filterMissions(sampleMissions, "completed")).toHaveLength(1);
  });

  it("filters missions by search query on title and ID", () => {
    const titleMatch = filterMissions(sampleMissions, "all", "backup");
    expect(titleMatch).toHaveLength(1);
    expect(titleMatch[0].id).toBe("m-4");

    const idMatch = filterMissions(sampleMissions, "all", "m-2");
    expect(idMatch).toHaveLength(1);
    expect(idMatch[0].title).toBe("Ανάλυση αρχείων καταγραφής");

    const noMatch = filterMissions(sampleMissions, "all", "ανύπαρκτο");
    expect(noMatch).toHaveLength(0);
  });

  it("combines active tab filter with query", () => {
    const combined = filterMissions(sampleMissions, "active", "σάρωση");
    expect(combined).toHaveLength(1);
    expect(combined[0].id).toBe("m-1");

    const wrongTabMatch = filterMissions(sampleMissions, "completed", "σάρωση");
    expect(wrongTabMatch).toHaveLength(0);
  });
});

describe("approval payload formatter", () => {
  it("handles empty or missing payloads gracefully", () => {
    expect(formatApprovalPayload(null)).toBe("—");
    expect(formatApprovalPayload(undefined)).toBe("—");
  });

  it("returns raw string payloads unchanged", () => {
    expect(formatApprovalPayload("git status")).toBe("git status");
  });

  it("formats structured objects as readable indented JSON", () => {
    const payload = { command: "npm test", timeout: 30 };
    const formatted = formatApprovalPayload(payload);
    expect(formatted).toContain('"command": "npm test"');
    expect(formatted).toContain('"timeout": 30');
    expect(JSON.parse(formatted)).toEqual(payload);
  });
});

describe("mission progress and run-next", () => {
  const raw = (status: string, tasks: Array<{ title: string; status: string }>) => ({
    id: 7,
    title: "Έλεγχος backup",
    status,
    tasks,
  });

  it("labels the backend mission statuses", () => {
    expect(missionStatusMeta("active").tone).toBe("active");
    expect(missionStatusMeta("blocked").tone).toBe("warn");
    expect(missionStatusMeta("waiting_approval").label).toBe("Θέλει έγκριση");
  });

  it("counts finished steps and picks the current one", () => {
    const mission = normalizeMission(
      raw("active", [
        { title: "Λήψη", status: "done" },
        { title: "Έλεγχος", status: "pending" },
        { title: "Αναφορά", status: "pending" },
      ]),
    );
    expect(mission).toMatchObject({
      id: "7",
      tasksDone: 1,
      tasksTotal: 3,
      currentStep: "Έλεγχος",
      currentStepStatus: "pending",
    });
    expect(canRunNextStep(mission!)).toBe(true);
  });

  it("does not offer run-next while a step waits, runs or failed", () => {
    for (const status of ["waiting_approval", "running", "needs_review", "failed"]) {
      const mission = normalizeMission(
        raw("blocked", [
          { title: "Πρώτο", status },
          { title: "Δεύτερο", status: "pending" },
        ]),
      )!;
      expect(mission.currentStep).toBe("Πρώτο");
      expect(canRunNextStep(mission)).toBe(false);
    }
    expect(canRunNextStep(normalizeMission(raw("done", [{ title: "x", status: "done" }]))!)).toBe(
      false,
    );
    expect(normalizeMission({ title: "χωρίς id" })).toBeNull();
  });

  it("describes run-next responses", () => {
    expect(describeRunNext({ ok: true, mission: { status: "active" } }).ok).toBe(true);
    expect(describeRunNext({ ok: true, mission: { status: "done" } }).message).toContain(
      "ολοκληρώθηκε",
    );
    expect(describeRunNext({ ok: false, approval_required: true }).message).toContain("έγκριση");
    expect(describeRunNext({ ok: false, busy: true }).ok).toBe(false);
    expect(describeRunNext({ ok: false, error: "mission_not_found" }).message).toContain(
      "δεν βρέθηκε",
    );
    expect(describeRunNext(null).ok).toBe(false);
  });
});
