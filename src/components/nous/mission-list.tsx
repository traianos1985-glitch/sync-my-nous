import { missionStatusMeta, missionToneClass } from "./mission-status";

export type LiveMission = { id: string; title: string; status: string };

export function MissionList({ missions }: { missions: LiveMission[] }) {
  if (missions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Δεν υπάρχουν ενεργά missions στο live stream.</p>
    );
  }
  return (
    <ul>
      {missions.map((mission) => {
        const meta = missionStatusMeta(mission.status);
        return (
          <li
            key={mission.id}
            className="flex items-center justify-between gap-3 border-b border-border/60 py-2 text-sm last:border-0"
          >
            <span className="min-w-0 truncate">{mission.title}</span>
            <span
              className={`shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-medium ${missionToneClass[meta.tone]}`}
            >
              {meta.active && meta.tone === "active" ? "● " : ""}
              {meta.label}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
