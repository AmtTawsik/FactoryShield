"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

/**
 * Filter values kept in the address bar, so a filtered list can be bookmarked, shared
 * and restored with the back button. Changing any filter other than `page` resets the page.
 */
export function useUrlFilters<K extends string>(keys: readonly K[]) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const values = useMemo(() => {
    const result = { page: Number(searchParams.get("page")) || 1 } as Record<K, string> & { page: number };
    for (const key of keys) (result as Record<string, string>)[key] = searchParams.get(key) ?? "";
    return result;
    // keys is a constant list declared by each page
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const update = useCallback(
    (changes: Partial<Record<K | "page", string | number>>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(changes)) {
        if (value === "" || value === undefined || value === null || (key === "page" && Number(value) <= 1)) {
          params.delete(key);
        } else {
          params.set(key, String(value));
        }
      }
      if (!("page" in changes)) params.delete("page");
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  const activeCount = keys.filter((key) => (values as Record<string, string>)[key]).length;
  const clear = useCallback(() => router.replace(pathname, { scroll: false }), [pathname, router]);

  return { values, update, clear, activeCount };
}
