"use client";

import { Clock } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input } from "@/components/ui/form";
import { InlineAlert } from "@/components/ui/states";
import { setReauthHandler } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";
import { signOut } from "./session";

const WARN_BEFORE_MS = 5 * 60 * 1000;

function readExpiry(): number | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)fs_expires=(\d+)/);
  return match ? Number(match[1]) : null;
}

export function SessionGuard({ user }: { user: CurrentUser }) {
  const [expiresAt, setExpiresAt] = useState<number | null>(readExpiry);
  const [now, setNow] = useState(() => Date.now());
  const [rejected, setRejected] = useState(false);
  const [renewing, setRenewing] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const waiters = useRef<((signedIn: boolean) => void)[]>([]);

  const settle = useCallback((signedIn: boolean) => {
    for (const resolve of waiters.current) resolve(signedIn);
    waiters.current = [];
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 15_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    setReauthHandler(
      () =>
        new Promise<boolean>((resolve) => {
          waiters.current.push(resolve);
          setRejected(true);
        }),
    );
    return () => setReauthHandler(null);
  }, []);

  const remaining = expiresAt === null ? null : expiresAt - now;
  const ended = rejected || (remaining !== null && remaining <= 0);
  const open = ended || renewing;

  async function signIn(event: FormEvent) {
    event.preventDefault();
    if (!password) {
      setError("Enter your password");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email, password }),
      });
      if (!response.ok) {
        setError(
          response.status === 401
            ? "Incorrect password, or the account has been deactivated."
            : "Sign in failed. Please try again.",
        );
        return;
      }
      setPassword("");
      setRejected(false);
      setRenewing(false);
      setExpiresAt(readExpiry());
      setNow(Date.now());
      settle(true);
    } catch {
      setError("Network error. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  async function leave() {
    settle(false);
    await signOut();
  }

  const minutesLeft = remaining === null ? null : Math.max(1, Math.ceil(remaining / 60_000));
  const showWarning = !open && remaining !== null && remaining > 0 && remaining <= WARN_BEFORE_MS;

  return (
    <>
      {showWarning && (
        <div
          role="status"
          className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-md border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-sm text-amber-900"
        >
          <Clock className="size-4 shrink-0" aria-hidden="true" />
          <span className="flex-1">
            Your session ends in {minutesLeft} minute{minutesLeft === 1 ? "" : "s"}. Sign in again to keep working
            without interruption.
          </span>
          <Button size="sm" variant="secondary" onClick={() => setRenewing(true)}>
            Stay signed in
          </Button>
        </div>
      )}

      <Dialog
        open={open}
        onClose={() => {
          if (!ended) setRenewing(false);
        }}
        busy={busy || ended}
        size="sm"
        title={ended ? "Your session has ended" : "Stay signed in"}
        description={
          ended
            ? "Sign in again to continue. This page and anything you have typed are kept."
            : "Enter your password to start a new session."
        }
        footer={
          <>
            <Button variant="ghost" onClick={leave} disabled={busy} className="mr-auto">
              Sign out
            </Button>
            {!ended && (
              <Button variant="secondary" onClick={() => setRenewing(false)} disabled={busy}>
                Not now
              </Button>
            )}
            <Button type="submit" form="reauth-form" loading={busy}>
              Sign in
            </Button>
          </>
        }
      >
        <form id="reauth-form" onSubmit={signIn} noValidate className="space-y-4">
          {error && <InlineAlert>{error}</InlineAlert>}
          <Field label="Email">
            <Input value={user.email} readOnly disabled />
          </Field>
          <Field label="Password">
            <Input
              type="password"
              autoComplete="current-password"
              autoFocus
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>
        </form>
      </Dialog>
    </>
  );
}
