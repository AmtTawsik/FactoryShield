"use client";

import { createContext, use, type ReactNode } from "react";
import type { CurrentUser } from "@/lib/types";

const SessionContext = createContext<CurrentUser | null>(null);

export function SessionProvider({ user, children }: { user: CurrentUser; children: ReactNode }) {
  return <SessionContext value={user}>{children}</SessionContext>;
}

export function useSession() {
  const user = use(SessionContext);
  if (!user) throw new Error("useSession must be used inside SessionProvider");
  return {
    user,
    isAdmin: user.role === "admin",
    isSuperAdmin: user.role === "super_admin",
  };
}

export async function signOut() {
  await fetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
  window.location.replace("/login");
}
