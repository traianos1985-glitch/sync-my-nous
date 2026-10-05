import { useState, useEffect, useCallback } from "react";

export interface AgentJournalEntry {
  id: number;
  time: number;
  event: string;
  data: Record<string, unknown>;
  hash?: string;
}

export function useAgentStream(streamUrl = "/api/missions/stream") {
  const [entries, setEntries] = useState<AgentJournalEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastPing, setLastPing] = useState<number | null>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(streamUrl);

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.addEventListener("missions", (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as { missions?: Array<Record<string, unknown>> };
          const newEntries: AgentJournalEntry[] = (data.missions ?? []).map((mission, index) => ({
            id: Date.now() + index,
            time: Date.now(),
            event: "mission_update",
            data: mission,
          }));
          if (newEntries.length)
            setEntries((prev) => [...prev, ...newEntries].slice(-200));
        } catch (err) {
          console.error("Error parsing agent stream data", err);
        }
      });

      eventSource.addEventListener("ping", (event: MessageEvent) => {
        try {
          const pingData = JSON.parse(event.data);
          setLastPing(pingData.time || Date.now());
        } catch {
          setLastPing(Date.now());
        }
      });

      eventSource.onerror = () => {
        setIsConnected(false);
      };
    } catch (err) {
      console.error("Failed to connect to agent stream", err);
      setIsConnected(false);
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [streamUrl]);

  const clearEntries = useCallback(() => {
    setEntries([]);
  }, []);

  return { entries, isConnected, lastPing, clearEntries };
}
