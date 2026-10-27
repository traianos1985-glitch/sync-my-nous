export const REQUEST_TIMEOUT_MS = 75_000;
export const SLOW_REQUEST_MS = 4_000;
export const RECOVERY_DELAY_MS = 1_200;
export const GATEWAY_STATUSES = new Set([502, 503, 504]);
export type BackendWakeState = {
  phase: "idle" | "waiting" | "recovering";
  pending: number;
  slow: number;
  gatewayFailures: number;
};

// Individual request IDs keep concurrent success, cancellation and failure independent.
export function createBackendWakeTracker() {
  let nextId = 0;
  const pending = new Set<number>();
  const slow = new Set<number>();
  let gatewayFailures = 0;
  const listeners = new Set<() => void>();
  let state: BackendWakeState = { phase: "idle", pending: 0, slow: 0, gatewayFailures: 0 };
  const emit = () => {
    state = {
      phase: slow.size > 0 ? "waiting" : gatewayFailures >= 2 ? "recovering" : "idle",
      pending: pending.size,
      slow: slow.size,
      gatewayFailures,
    };
    listeners.forEach((listener) => listener());
  };
  return {
    getSnapshot: () => state,
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    begin() {
      const id = ++nextId;
      pending.add(id);
      emit();
      return id;
    },
    markSlow(id: number) {
      if (pending.has(id)) {
        slow.add(id);
        emit();
      }
    },
    gatewayFailure() {
      gatewayFailures += 1;
      emit();
    },
    reachable() {
      gatewayFailures = 0;
      emit();
    },
    finish(id: number) {
      pending.delete(id);
      slow.delete(id);
      emit();
    },
  };
}
export const backendWakeTracker = createBackendWakeTracker();
export const idleBackendWakeState: BackendWakeState = {
  phase: "idle",
  pending: 0,
  slow: 0,
  gatewayFailures: 0,
};
