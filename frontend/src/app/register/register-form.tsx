"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/form";
import { InlineAlert } from "@/components/ui/states";

type Form = { organization_name: string; full_name: string; email: string; password: string };
type Errors = Partial<Record<keyof Form, string>>;

function validate(form: Form): Errors {
  const errors: Errors = {};
  if (form.organization_name.trim().length < 2) errors.organization_name = "Enter your company or group name";
  if (form.full_name.trim().length < 2) errors.full_name = "Enter your full name";
  if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) errors.email = "Enter a valid email address";
  if (form.password.length < 8) errors.password = "Use at least 8 characters";
  else if (!/[a-zA-Z]/.test(form.password) || !/\d/.test(form.password)) {
    errors.password = "Use at least one letter and one number";
  }
  return errors;
}

export function RegisterForm() {
  const [form, setForm] = useState<Form>({ organization_name: "", full_name: "", email: "", password: "" });
  const [errors, setErrors] = useState<Errors>({});
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (key: keyof Form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [key]: event.target.value });

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, email: form.email.trim() }),
      });
      if (response.ok) {
        window.location.replace("/");
        return;
      }
      const body = await response.json().catch(() => null);
      if (response.status === 422 && Array.isArray(body?.errors)) {
        const fieldErrors: Errors = {};
        for (const item of body.errors as { field: string; message: string }[]) {
          const key = item.field.split(".").at(-1) as keyof Form;
          fieldErrors[key] ??= item.message;
        }
        setErrors(fieldErrors);
        setError("Please correct the highlighted fields.");
      } else {
        setError(body?.detail ?? "Sign up failed. Please try again.");
      }
    } catch {
      setError("Network error. Check your connection and try again.");
    }
    setLoading(false);
  }

  return (
    <form onSubmit={submit} noValidate className="mt-8 space-y-5">
      {error && <InlineAlert>{error}</InlineAlert>}
      <Field label="Company or group name" required error={errors.organization_name}>
        <Input
          value={form.organization_name}
          onChange={set("organization_name")}
          autoFocus
          maxLength={150}
          placeholder="e.g. Rupali Apparel Group"
        />
      </Field>
      <Field label="Your full name" required error={errors.full_name}>
        <Input value={form.full_name} onChange={set("full_name")} autoComplete="name" maxLength={120} />
      </Field>
      <Field label="Work email" required error={errors.email}>
        <Input
          type="email"
          value={form.email}
          onChange={set("email")}
          autoComplete="email"
          maxLength={255}
          placeholder="name@company.com"
        />
      </Field>
      <Field label="Password" required error={errors.password} hint="8+ characters with a letter and a number">
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            value={form.password}
            onChange={set("password")}
            autoComplete="new-password"
            maxLength={128}
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
        Create account
      </Button>
    </form>
  );
}
