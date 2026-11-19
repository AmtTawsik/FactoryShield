"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, DetailList, PageHeader } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/form";
import { InlineAlert } from "@/components/ui/states";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useSubmit } from "@/hooks/use-submit";
import { api } from "@/lib/api";
import { USER_ROLE } from "@/lib/labels";

const EMPTY = { current_password: "", new_password: "", confirm: "" };

function ChangePassword() {
  const [form, setForm] = useState(EMPTY);
  const [visible, setVisible] = useState(false);
  const { run, saving, error, fieldErrors } = useSubmit();
  const toast = useToast();

  function validate() {
    const errors: Record<string, string> = {};
    if (!form.current_password) errors.current_password = "Enter your current password";
    if (form.new_password.length < 8) errors.new_password = "Use at least 8 characters";
    else if (!/[a-zA-Z]/.test(form.new_password) || !/\d/.test(form.new_password)) {
      errors.new_password = "Use at least one letter and one number";
    } else if (form.new_password === form.current_password) {
      errors.new_password = "Choose a password different from the current one";
    }
    if (form.confirm !== form.new_password) errors.confirm = "The passwords do not match";
    return errors;
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const done = await run(
      () =>
        api<void>("/auth/change-password", {
          method: "POST",
          body: { current_password: form.current_password, new_password: form.new_password },
        }).then(() => true),
      validate(),
    );
    if (!done) return;
    setForm(EMPTY);
    toast.success("Password changed. Use the new password next time you sign in.");
  }

  const currentError =
    fieldErrors.current_password ?? (error === "Current password is incorrect" ? error : undefined);
  const generalError = error === "Current password is incorrect" ? null : error;
  const type = visible ? "text" : "password";

  return (
    <Card>
      <CardHeader title="Change password" description="Use at least 8 characters with a letter and a number." />
      <form onSubmit={submit} noValidate className="max-w-md space-y-4 p-4">
        {generalError && <InlineAlert>{generalError}</InlineAlert>}
        <Field label="Current password" required error={currentError}>
          <Input
            type={type}
            autoComplete="current-password"
            value={form.current_password}
            onChange={(event) => setForm({ ...form, current_password: event.target.value })}
            maxLength={128}
          />
        </Field>
        <Field label="New password" required error={fieldErrors.new_password}>
          <Input
            type={type}
            autoComplete="new-password"
            value={form.new_password}
            onChange={(event) => setForm({ ...form, new_password: event.target.value })}
            maxLength={128}
          />
        </Field>
        <Field label="Confirm new password" required error={fieldErrors.confirm}>
          <Input
            type={type}
            autoComplete="new-password"
            value={form.confirm}
            onChange={(event) => setForm({ ...form, confirm: event.target.value })}
            maxLength={128}
          />
        </Field>
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" loading={saving}>
            Change password
          </Button>
          <button
            type="button"
            onClick={() => setVisible((value) => !value)}
            aria-pressed={visible}
            className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900"
          >
            {visible ? <EyeOff className="size-4" aria-hidden="true" /> : <Eye className="size-4" aria-hidden="true" />}
            {visible ? "Hide passwords" : "Show passwords"}
          </button>
        </div>
        <p className="text-xs text-slate-500">
          Other browsers where you are signed in stay signed in until their session ends (at most one hour).
        </p>
      </form>
    </Card>
  );
}

export function AccountView() {
  const { user, isAdmin, isSuperAdmin } = useSession();
  const factories = useAllFactories(!isSuperAdmin);

  return (
    <>
      <PageHeader title="My account" description="Your details and password." />
      <div className="space-y-6">
        <Card>
          <CardHeader title="Profile" description="Ask an administrator to change your name, email or role." />
          <div className="p-4">
            <DetailList
              items={[
                { label: "Name", value: user.full_name },
                { label: "Organization", value: user.organization?.name ?? "Platform administration" },
                { label: "Email", value: user.email },
                { label: "Role", value: <Badge tone={isAdmin ? "brand" : "neutral"}>{USER_ROLE[user.role]}</Badge> },
                {
                  label: "Factory access",
                  value: isSuperAdmin
                    ? "None. The platform administrator does not see organization records."
                    : isAdmin
                    ? "All factories of your organization"
                    : factories.isLoading
                      ? "Loading…"
                      : factories.factories.length
                        ? factories.factories.map((factory) => factory.name).join(", ")
                        : "None assigned yet",
                },
              ]}
            />
          </div>
        </Card>
        <ChangePassword />
      </div>
    </>
  );
}
