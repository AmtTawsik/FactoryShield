"use client";

import { useMemo, useState } from "react";
import { FormDialog } from "@/components/ui/dialog";
import { Checkbox, Field, FieldGroup, Input, Select } from "@/components/ui/form";
import { InlineAlert } from "@/components/ui/states";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useSubmit } from "@/hooks/use-submit";
import { api } from "@/lib/api";
import { OPTIONS } from "@/lib/labels";
import type { UserDetail, UserRole } from "@/lib/types";

function passwordProblem(password: string): string | undefined {
  if (password.length < 8) return "Use at least 8 characters";
  if (!/[a-zA-Z]/.test(password) || !/\d/.test(password)) return "Use at least one letter and one number";
  return undefined;
}

function FactoryPicker({ selected, onChange }: { selected: number[]; onChange: (ids: number[]) => void }) {
  const factories = useAllFactories();
  const [filter, setFilter] = useState("");
  const visible = factories.factories.filter((factory) => factory.name.toLowerCase().includes(filter.toLowerCase()));
  const chosen = new Set(selected);

  function toggle(id: number) {
    const next = new Set(chosen);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange([...next]);
  }

  return (
    <div className="rounded-md border border-slate-300">
      <div className="flex items-center gap-2 border-b border-slate-200 p-2">
        <input
          type="search"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="Filter factories"
          aria-label="Filter factories"
          className="h-8 flex-1 rounded-md border border-slate-300 px-2.5 text-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 focus:outline-none"
        />
        <span className="shrink-0 text-xs text-slate-500">{selected.length} selected</span>
      </div>
      <div className="max-h-56 space-y-2 overflow-y-auto p-3">
        {factories.isLoading ? (
          <p className="text-sm text-slate-500">Loading factories…</p>
        ) : visible.length === 0 ? (
          <p className="text-sm text-slate-500">No factories found</p>
        ) : (
          visible.map((factory) => (
            <Checkbox
              key={factory.id}
              label={factory.name}
              description={`${factory.district}${factory.is_active ? "" : " · inactive"}`}
              checked={chosen.has(factory.id)}
              onChange={() => toggle(factory.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

export function CreateUserDialog({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "staff" as UserRole });
  const [factoryIds, setFactoryIds] = useState<number[]>([]);
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  async function submit() {
    const errors: Record<string, string> = {};
    if (form.full_name.trim().length < 2) errors.full_name = "Enter the full name";
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) errors.email = "Enter a valid email address";
    const problem = passwordProblem(form.password);
    if (problem) errors.password = problem;

    const saved = await run(
      () =>
        api<UserDetail>("/users", {
          method: "POST",
          body: { ...form, factory_ids: form.role === "staff" ? factoryIds : [] },
        }),
      errors,
    );
    if (!saved) return;
    await revalidate("/users");
    toast.success(`${saved.full_name} can now sign in`);
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title="Add user"
      description="Share the email and starting password with the person directly."
      onSubmit={submit}
      submitLabel="Add user"
      saving={saving}
      error={error}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Full name" required error={fieldErrors.full_name} className="sm:col-span-2">
          <Input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} maxLength={120} />
        </Field>
        <Field label="Email" required error={fieldErrors.email}>
          <Input
            type="email"
            autoComplete="off"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            maxLength={255}
          />
        </Field>
        <Field label="Starting password" required error={fieldErrors.password} hint="8+ characters with a letter and a number">
          <Input
            type="text"
            autoComplete="new-password"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            maxLength={128}
          />
        </Field>
        <Field label="Role" required error={fieldErrors.role} className="sm:col-span-2">
          <Select
            value={form.role}
            onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
            options={OPTIONS.userRole}
          />
        </Field>
      </div>
      {form.role === "admin" ? (
        <InlineAlert tone="info">Admins can see and change every factory, and manage users.</InlineAlert>
      ) : (
        <FieldGroup label="Factories" error={fieldErrors.factory_ids} hint="Staff see only these factories (read-only).">
          <FactoryPicker selected={factoryIds} onChange={setFactoryIds} />
        </FieldGroup>
      )}
    </FormDialog>
  );
}

export function EditUserDialog({ user, isSelf, onClose }: { user: UserDetail; isSelf: boolean; onClose: () => void }) {
  const [form, setForm] = useState({ full_name: user.full_name, role: user.role, is_active: user.is_active, password: "" });
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  async function submit() {
    const errors: Record<string, string> = {};
    if (form.full_name.trim().length < 2) errors.full_name = "Enter the full name";
    if (form.password) {
      const problem = passwordProblem(form.password);
      if (problem) errors.password = problem;
    }
    const changes: Record<string, unknown> = {};
    if (form.full_name.trim() !== user.full_name) changes.full_name = form.full_name.trim();
    if (form.role !== user.role) changes.role = form.role;
    if (form.is_active !== user.is_active) changes.is_active = form.is_active;
    if (form.password) changes.password = form.password;

    if (Object.keys(changes).length === 0 && Object.keys(errors).length === 0) {
      onClose();
      return;
    }
    const saved = await run(() => api<UserDetail>(`/users/${user.id}`, { method: "PATCH", body: changes }), errors);
    if (!saved) return;
    await revalidate("/users", "/auth/me");
    toast.success(changes.password ? "User updated and password changed" : "User updated");
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title="Edit user"
      description={user.email}
      onSubmit={submit}
      submitLabel="Save changes"
      saving={saving}
      error={error}
    >
      <Field label="Full name" required error={fieldErrors.full_name}>
        <Input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} maxLength={120} />
      </Field>
      <Field
        label="Role"
        required
        error={fieldErrors.role}
        hint={isSelf ? "You cannot remove your own admin role." : undefined}
      >
        <Select
          value={form.role}
          onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
          options={OPTIONS.userRole}
          disabled={isSelf}
        />
      </Field>
      <Field label="New password" error={fieldErrors.password} hint="Leave empty to keep the current password">
        <Input
          type="text"
          autoComplete="new-password"
          value={form.password}
          onChange={(event) => setForm({ ...form, password: event.target.value })}
          maxLength={128}
        />
      </Field>
      <Checkbox
        label="Active"
        description={
          isSelf ? "You cannot deactivate your own account." : "Deactivated users cannot sign in. Their records keep their name."
        }
        checked={form.is_active}
        disabled={isSelf}
        onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
      />
    </FormDialog>
  );
}

export function FactoriesDialog({ user, onClose }: { user: UserDetail; onClose: () => void }) {
  const [selected, setSelected] = useState<number[]>(user.factory_ids);
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();
  const unchanged = useMemo(
    () => [...selected].sort().join() === [...user.factory_ids].sort().join(),
    [selected, user.factory_ids],
  );

  async function submit() {
    if (unchanged) {
      onClose();
      return;
    }
    const saved = await run(() =>
      api<UserDetail>(`/users/${user.id}/factories`, { method: "PUT", body: { factory_ids: selected } }),
    );
    if (!saved) return;
    await revalidate("/users");
    toast.success(`Factory access updated for ${user.full_name}`);
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title="Assign factories"
      description={`${user.full_name} will see only the selected factories.`}
      onSubmit={submit}
      submitLabel="Save assignments"
      saving={saving}
      error={error}
    >
      {user.role === "admin" && (
        <InlineAlert tone="info">This user is an admin and can already see every factory. Assignments apply if the role changes to staff.</InlineAlert>
      )}
      <FieldGroup label="Factories" error={fieldErrors.factory_ids}>
        <FactoryPicker selected={selected} onChange={setSelected} />
      </FieldGroup>
    </FormDialog>
  );
}
