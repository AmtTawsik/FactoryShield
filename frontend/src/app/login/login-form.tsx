"use client";

import { Eye, EyeOff } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";
import { InlineAlert } from "@/components/ui/states";

function safeNext(value: string | null): string {
  // browsers treat "/\evil.com" like "//evil.com"
  return value && value.startsWith("/") && !value.startsWith("//") && !value.includes("\\") ? value : "/";
}

export function LoginForm() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const errors: typeof fieldErrors = {};
    if (!email.trim()) errors.email = "Enter your email address";
    else if (!/^\S+@\S+\.\S+$/.test(email.trim())) errors.email = "Enter a valid email address";
    if (!password) errors.password = "Enter your password";
    setFieldErrors(errors);
    if (errors.email || errors.password) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (response.ok) {
        window.location.assign(safeNext(searchParams.get("next")));
        return;
      }
      const body = await response.json().catch(() => null);
      setError(
        response.status === 401
          ? "Incorrect email or password, or the account is deactivated."
          : response.status === 422
            ? "Enter a valid email address and password."
            : (body?.detail ?? "Sign in failed. Please try again."),
      );
    } catch {
      setError("Network error. Check your connection and try again.");
    }
    setLoading(false);
  }

  return (
    <form onSubmit={submit} noValidate className="mt-8 space-y-5">
      {error && <InlineAlert>{error}</InlineAlert>}
      <Field label="Email" error={fieldErrors.email}>
        <Input
          type="email"
          autoComplete="email"
          autoFocus
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="name@company.com"
        />
      </Field>
      <Field label="Password" error={fieldErrors.password}>
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="pr-10"
          />
          <button
            type="button"
            onClick={() => setShowPassword((value) => !value)}
            className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-slate-400 hover:text-slate-600"
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
          >
            {showPassword ? <EyeOff className="size-4" aria-hidden="true" /> : <Eye className="size-4" aria-hidden="true" />}
          </button>
        </div>
      </Field>
      <Button type="submit" loading={loading} className="w-full">
        Sign in
      </Button>
    </form>
  );
}
