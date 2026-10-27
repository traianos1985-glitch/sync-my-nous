import { useCallback, useEffect, useRef } from "react";
import { nousFetch, type NousApiOptions } from "@/lib/nous-api";

// Cancel every dashboard-owned request at unmount; coalesce identical reads only.
export function useDashboardRequests() {
  const controllers = useRef(new Set<AbortController>());
  const reads = useRef(new Map<string, Promise<unknown>>());
  useEffect(
    () => () => {
      controllers.current.forEach((controller) => controller.abort());
      controllers.current.clear();
      reads.current.clear();
    },
    [],
  );
  return useCallback(<T>(path: string, options: NousApiOptions = {}): Promise<T> => {
    const read = (options.method ?? "GET").toUpperCase() === "GET";
    const existing = read && !options.signal ? reads.current.get(path) : undefined;
    if (existing) return existing as Promise<T>;
    const controller = new AbortController();
    const signal = options.signal;
    const abort = () => controller.abort(signal?.reason);
    if (signal?.aborted) abort();
    else signal?.addEventListener("abort", abort, { once: true });
    controllers.current.add(controller);
    const promise = nousFetch<T>(path, { ...options, signal: controller.signal }).finally(() => {
      signal?.removeEventListener("abort", abort);
      controllers.current.delete(controller);
      if (reads.current.get(path) === promise) reads.current.delete(path);
    });
    if (read && !options.signal) reads.current.set(path, promise);
    return promise;
  }, []);
}
