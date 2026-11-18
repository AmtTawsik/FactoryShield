"use client";

import { useMemo } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import type { Factory, Page } from "@/lib/types";

export const ALL_FACTORIES_KEY = "factories:all";

async function loadAllFactories(): Promise<Factory[]> {
  const all: Factory[] = [];
  for (let page = 1; ; page++) {
    const result = await api<Page<Factory>>("/factories", { query: { page, size: 100 } });
    all.push(...result.items);
    if (all.length >= result.total || result.items.length === 0) return all;
  }
}

/** Every factory the user can see (used for names in tables and for pickers). */
export function useAllFactories() {
  const { data, error, isLoading, mutate } = useSWR(ALL_FACTORIES_KEY, loadAllFactories, {
    revalidateOnFocus: false,
  });

  return useMemo(() => {
    const factories = [...(data ?? [])].sort((a, b) => a.name.localeCompare(b.name));
    const byId = new Map(factories.map((factory) => [factory.id, factory]));
    return {
      factories,
      byId,
      nameOf: (id: number | null | undefined) => (id ? (byId.get(id)?.name ?? `Factory #${id}`) : "—"),
      options: factories.map((factory) => ({
        value: String(factory.id),
        label: factory.is_active ? factory.name : `${factory.name} (inactive)`,
      })),
      error,
      isLoading,
      mutate,
    };
  }, [data, error, isLoading, mutate]);
}
