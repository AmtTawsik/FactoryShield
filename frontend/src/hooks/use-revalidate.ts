"use client";

import { useCallback } from "react";
import { useSWRConfig } from "swr";
import { ALL_FACTORIES_KEY } from "./use-factories";

/**
 * Refreshes every cached request whose key starts with one of the given paths,
 * plus the dashboard (its numbers depend on all records).
 */
export function useRevalidate() {
  const { mutate } = useSWRConfig();
  return useCallback(
    (...prefixes: string[]) => {
      const all = [...prefixes, "/dashboard"];
      if (prefixes.includes("/factories")) all.push(ALL_FACTORIES_KEY);
      return mutate((key) => typeof key === "string" && all.some((prefix) => key.startsWith(prefix)));
    },
    [mutate],
  );
}
