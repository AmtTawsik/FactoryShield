"use client";

import {
  BookOpen,
  Building2,
  Building,
  ClipboardCheck,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  MessageSquareText,
  TriangleAlert,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import useSWR, { SWRConfig } from "swr";
import { ApiError, errorMessage, fetcher } from "@/lib/api";
import { cn } from "@/lib/cn";
import { USER_ROLE } from "@/lib/labels";
import type { CurrentUser } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { ErrorState, Spinner } from "@/components/ui/states";
import { ToastProvider } from "@/components/ui/toast";
import { Logo } from "./logo";
import { SessionGuard } from "./session-guard";
import { SessionProvider, signOut } from "./session";

type NavItem = { href: string; label: string; icon: typeof LayoutDashboard; adminOnly?: boolean };
type NavSection = { heading?: string; items: NavItem[] };

const ORGANIZATION_NAV: NavSection[] = [
  { items: [{ href: "/", label: "Dashboard", icon: LayoutDashboard }] },
  {
    heading: "Operations",
    items: [
      { href: "/factories", label: "Factories", icon: Building2 },
      { href: "/inspections", label: "Safety inspections", icon: ClipboardCheck },
      { href: "/incidents", label: "Incidents", icon: TriangleAlert },
      { href: "/actions", label: "Corrective actions", icon: ListChecks },
    ],
  },
  {
    heading: "Knowledge",
    items: [
      { href: "/knowledge", label: "Knowledge documents", icon: BookOpen },
      { href: "/assistant", label: "AI Assistant", icon: MessageSquareText },
    ],
  },
  { heading: "Administration", items: [{ href: "/users", label: "User management", icon: Users, adminOnly: true }] },
];

const PLATFORM_NAV: NavSection[] = [
  {
    heading: "Platform",
    items: [
      { href: "/organizations", label: "Organizations", icon: Building },
      { href: "/knowledge", label: "Shared library", icon: BookOpen },
    ],
  },
];

const PLATFORM_PATHS = ["/organizations", "/knowledge", "/account"];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function Sidebar({ user, onNavigate }: { user: CurrentUser; onNavigate?: () => void }) {
  const pathname = usePathname();
  const isAdmin = user.role === "admin";
  const nav = user.role === "super_admin" ? PLATFORM_NAV : ORGANIZATION_NAV;

  return (
    <div className="flex h-full flex-col bg-brand-900 text-brand-100">
      <div className="flex h-14 items-center px-4">
        <Link href="/" onClick={onNavigate} aria-label="FactoryShield home">
          <Logo inverted />
        </Link>
      </div>
      <div className="mx-3 rounded-md bg-white/6 px-3 py-2">
        <p className="text-[11px] font-medium tracking-wider text-brand-300/80 uppercase">
          {user.organization ? "Organization" : "Signed in as"}
        </p>
        <p className="truncate text-sm font-medium text-white" title={user.organization?.name}>
          {user.organization?.name ?? "Platform administration"}
        </p>
      </div>
      <nav aria-label="Main" className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {nav.map((section, index) => {
          const items = section.items.filter((item) => !item.adminOnly || isAdmin);
          if (items.length === 0) return null;
          return (
            <div key={section.heading ?? index}>
              {section.heading && (
                <p className="mb-1.5 px-2 text-[11px] font-semibold tracking-wider text-brand-300/80 uppercase">
                  {section.heading}
                </p>
              )}
              <ul className="space-y-0.5">
                {items.map((item) => {
                  const active = isActive(pathname, item.href);
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={onNavigate}
                        aria-current={active ? "page" : undefined}
                        className={cn(
                          "flex items-center gap-2.5 rounded-md px-2 py-2 text-sm font-medium transition-colors",
                          active ? "bg-white/12 text-white" : "text-brand-100/85 hover:bg-white/6 hover:text-white",
                        )}
                      >
                        <item.icon className="size-4 shrink-0" aria-hidden="true" />
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>
      <div className="border-t border-white/10 p-3">
        <div className="flex items-center gap-1">
          <Link
            href="/account"
            onClick={onNavigate}
            aria-current={isActive(pathname, "/account") ? "page" : undefined}
            title="My account"
            className={cn(
              "flex min-w-0 flex-1 items-center gap-2.5 rounded-md p-1 transition-colors",
              isActive(pathname, "/account") ? "bg-white/12" : "hover:bg-white/6",
            )}
          >
            <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs font-semibold text-white">
              {initials(user.full_name)}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-white">{user.full_name}</span>
              <span className="block truncate text-xs text-brand-200/80">{USER_ROLE[user.role]}</span>
            </span>
          </Link>
          <button
            type="button"
            onClick={signOut}
            className="rounded-md p-1.5 text-brand-200 hover:bg-white/10 hover:text-white"
            aria-label="Sign out"
            title="Sign out"
          >
            <LogOut className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}

function MobileNav({ user }: { user: CurrentUser }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 lg:hidden">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="-ml-1.5 rounded-md p-1.5 text-slate-600 hover:bg-slate-100"
          aria-label="Open navigation"
          aria-expanded={open}
        >
          <Menu className="size-5" aria-hidden="true" />
        </button>
        <Link href="/">
          <Logo />
        </Link>
        <span className="w-8" />
      </header>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85%]" key={pathname}>
            <Sidebar user={user} onNavigate={() => setOpen(false)} />
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="absolute top-3 -right-11 rounded-md p-1.5 text-white hover:bg-white/10"
              aria-label="Close navigation"
            >
              <X className="size-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function PlatformGuard({ user, children }: { user: CurrentUser; children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const blocked = user.role === "super_admin" && !PLATFORM_PATHS.some((path) => isActive(pathname, path));

  useEffect(() => {
    if (blocked) router.replace("/organizations");
  }, [blocked, router]);

  if (blocked) {
    return (
      <div role="status" className="flex items-center gap-2 py-12 text-sm text-slate-500">
        <Spinner className="size-4" />
        Opening organizations…
      </div>
    );
  }
  return <>{children}</>;
}

function FullPage({ children }: { children: ReactNode }) {
  return <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">{children}</div>;
}

export function AppShell({ children }: { children: ReactNode }) {
  const { data: user, error, isLoading, mutate } = useSWR<CurrentUser>("/auth/me", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

  if (isLoading || (error instanceof ApiError && error.status === 401)) {
    return (
      <FullPage>
        <div role="status" className="flex items-center gap-2 text-sm text-slate-500">
          <Spinner className="size-4" />
          Loading your workspace…
        </div>
      </FullPage>
    );
  }

  if (error || !user) {
    return (
      <FullPage>
        <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white">
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
          <div className="border-t border-slate-200 px-4 py-3 text-center">
            <Button variant="ghost" size="sm" onClick={signOut}>
              Sign out
            </Button>
          </div>
        </div>
      </FullPage>
    );
  }

  return (
    <SessionProvider user={user}>
      <ToastProvider>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:shadow"
        >
          Skip to content
        </a>
        <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 lg:block">
          <Sidebar user={user} />
        </aside>
        <MobileNav user={user} />
        <main id="main" className="min-w-0 lg:pl-64">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <SessionGuard user={user} />
            <PlatformGuard user={user}>{children}</PlatformGuard>
          </div>
        </main>
      </ToastProvider>
    </SessionProvider>
  );
}

export function SwrProvider({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        keepPreviousData: true,
        shouldRetryOnError: (error) => !(error instanceof ApiError) || error.status >= 500 || error.status === 0,
        errorRetryCount: 2,
      }}
    >
      {children}
    </SWRConfig>
  );
}
