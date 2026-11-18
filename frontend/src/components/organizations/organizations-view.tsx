"use client";

import { Building, Lock, Pencil, Plus, UserPlus } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, PageHeader } from "@/components/ui/card";
import { FormDialog } from "@/components/ui/dialog";
import { Checkbox, Field, FilterSelect, Input } from "@/components/ui/form";
import { FilterBar, SearchInput } from "@/components/ui/search-input";
import { EmptyState, ErrorState, InlineAlert, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useSubmit } from "@/hooks/use-submit";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { api, errorMessage, withQuery } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { OrganizationDetail, OrganizationItem, Page } from "@/lib/types";

const FILTERS = ["search", "is_active"] as const;

type Account = { full_name: string; email: string; password: string };
const EMPTY_ACCOUNT: Account = { full_name: "", email: "", password: "" };

function checkAccount(account: Account): Record<string, string> {
  const errors: Record<string, string> = {};
  if (account.full_name.trim().length < 2) errors.full_name = "Enter the admin's full name";
  if (!/^\S+@\S+\.\S+$/.test(account.email.trim())) errors.email = "Enter a valid email address";
  if (account.password.length < 8) errors.password = "Use at least 8 characters";
  else if (!/[a-zA-Z]/.test(account.password) || !/\d/.test(account.password)) {
    errors.password = "Use at least one letter and one number";
  }
  return errors;
}

function AccountFields({
  account,
  onChange,
  errors,
}: {
  account: Account;
  onChange: (account: Account) => void;
  errors: Record<string, string>;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="Admin's full name" required error={errors.full_name} className="sm:col-span-2">
        <Input value={account.full_name} onChange={(e) => onChange({ ...account, full_name: e.target.value })} maxLength={120} />
      </Field>
      <Field label="Admin's email" required error={errors.email}>
        <Input
          type="email"
          autoComplete="off"
          value={account.email}
          onChange={(e) => onChange({ ...account, email: e.target.value })}
          maxLength={255}
        />
      </Field>
      <Field label="Starting password" required error={errors.password} hint="8+ characters with a letter and a number">
        <Input
          type="text"
          autoComplete="new-password"
          value={account.password}
          onChange={(e) => onChange({ ...account, password: e.target.value })}
          maxLength={128}
        />
      </Field>
    </div>
  );
}

function CreateOrganizationDialog({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [admin, setAdmin] = useState<Account>(EMPTY_ACCOUNT);
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  async function submit() {
    const errors = checkAccount(admin);
    if (name.trim().length < 2) errors.name = "Enter the organization name";
    const saved = await run(
      () => api<OrganizationDetail>("/organizations", { method: "POST", body: { name, admin } }),
      errors,
    );
    if (!saved) return;
    await revalidate("/organizations");
    toast.success(`${saved.name} created. Share the admin's sign-in details with them directly.`);
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title="New organization"
      description="A customer company. Its first admin adds factories and staff."
      onSubmit={submit}
      submitLabel="Create organization"
      saving={saving}
      error={error}
    >
      <Field label="Organization name" required error={fieldErrors.name}>
        <Input value={name} onChange={(e) => setName(e.target.value)} maxLength={150} placeholder="e.g. Rupali Apparel Group" />
      </Field>
      <p className="pt-2 text-sm font-medium text-slate-900">First admin</p>
      <AccountFields account={admin} onChange={setAdmin} errors={fieldErrors} />
    </FormDialog>
  );
}

function EditOrganizationDialog({ organization, onClose }: { organization: OrganizationItem; onClose: () => void }) {
  const [name, setName] = useState(organization.name);
  const [active, setActive] = useState(organization.is_active);
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  async function submit() {
    const changes: Record<string, unknown> = {};
    if (name.trim() !== organization.name) changes.name = name.trim();
    if (active !== organization.is_active) changes.is_active = active;
    if (Object.keys(changes).length === 0) {
      onClose();
      return;
    }
    const errors: Record<string, string> = name.trim().length < 2 ? { name: "Enter the organization name" } : {};
    const saved = await run(
      () => api<OrganizationDetail>(`/organizations/${organization.id}`, { method: "PATCH", body: changes }),
      errors,
    );
    if (!saved) return;
    await revalidate("/organizations");
    toast.success(
      changes.is_active === false
        ? `${saved.name} deactivated. Its users can no longer sign in.`
        : changes.is_active === true
          ? `${saved.name} reactivated`
          : "Organization updated",
    );
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title="Edit organization"
      description={organization.name}
      onSubmit={submit}
      submitLabel="Save changes"
      saving={saving}
      error={error}
    >
      <Field label="Organization name" required error={fieldErrors.name}>
        <Input value={name} onChange={(e) => setName(e.target.value)} maxLength={150} />
      </Field>
      <Checkbox
        label="Active"
        description="When off, nobody in this organization can sign in. Their records are kept."
        checked={active}
        onChange={(e) => setActive(e.target.checked)}
      />
      {organization.is_active && !active && (
        <InlineAlert tone="warning">
          {formatNumber(organization.user_count)} user{organization.user_count === 1 ? "" : "s"} will be signed out and
          blocked until you turn the organization back on.
        </InlineAlert>
      )}
    </FormDialog>
  );
}

function AddAdminDialog({ organization, onClose }: { organization: OrganizationItem; onClose: () => void }) {
  const { data } = useSWR<OrganizationDetail>(`/organizations/${organization.id}`);
  const [admin, setAdmin] = useState<Account>(EMPTY_ACCOUNT);
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  async function submit() {
    const saved = await run(
      () => api<OrganizationDetail>(`/organizations/${organization.id}/admins`, { method: "POST", body: admin }),
      checkAccount(admin),
    );
    if (!saved) return;
    await revalidate("/organizations");
    toast.success(`${admin.full_name.trim()} is now an admin of ${saved.name}`);
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title="Add an admin"
      description={`For ${organization.name}, e.g. when its admin has left.`}
      onSubmit={submit}
      submitLabel="Add admin"
      saving={saving}
      error={error}
    >
      <div>
        <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Current admins</p>
        <ul className="mt-1.5 space-y-1 text-sm">
          {!data ? (
            <li className="text-slate-500">Loading…</li>
          ) : data.admins.length === 0 ? (
            <li className="text-amber-700">No admin yet</li>
          ) : (
            data.admins.map((item) => (
              <li key={item.id} className="flex flex-wrap items-center gap-x-2">
                <span className="text-slate-900">{item.full_name}</span>
                <span className="text-slate-500">{item.email}</span>
                {!item.is_active && <Badge>Deactivated</Badge>}
              </li>
            ))
          )}
        </ul>
      </div>
      <AccountFields account={admin} onChange={setAdmin} errors={fieldErrors} />
    </FormDialog>
  );
}

function OrganizationsList() {
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const { data, error, isLoading, mutate } = useSWR<Page<OrganizationItem>>(withQuery("/organizations", values));
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<OrganizationItem | null>(null);
  const [addingAdmin, setAddingAdmin] = useState<OrganizationItem | null>(null);

  return (
    <>
      <PageHeader
        title="Organizations"
        description="Customer companies using FactoryShield. Their records stay private to them."
        actions={
          <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
            New organization
          </Button>
        }
      />

      <Card>
        <FilterBar activeCount={activeCount} onClear={clear}>
          <SearchInput
            value={values.search}
            onChange={(search) => update({ search })}
            placeholder="Search organizations"
            className="w-full sm:w-72"
          />
          <FilterSelect
            label="Status"
            value={values.is_active}
            onChange={(is_active) => update({ is_active })}
            options={[
              { value: "true", label: "Active" },
              { value: "false", label: "Deactivated" },
            ]}
            allLabel="Any status"
            className="w-full sm:w-40"
          />
        </FilterBar>

        {error ? (
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        ) : isLoading || !data ? (
          <TableSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={<Building className="size-5" aria-hidden="true" />}
            title={activeCount ? "No organizations match these filters" : "No organizations yet"}
            description={activeCount ? "Try a different search or clear the filters." : "Create one, or let companies sign up themselves."}
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Organization</Th>
                <Th className="text-right">Users</Th>
                <Th className="text-right">Factories</Th>
                <Th>Status</Th>
                <Th className="hidden md:table-cell">Created</Th>
                <Th className="w-24">
                  <span className="sr-only">Actions</span>
                </Th>
              </THead>
              <TBody>
                {data.items.map((organization) => (
                  <Tr key={organization.id}>
                    <Td className="font-medium text-slate-900">{organization.name}</Td>
                    <Td className="text-right tabular-nums">{formatNumber(organization.user_count)}</Td>
                    <Td className="text-right tabular-nums">{formatNumber(organization.factory_count)}</Td>
                    <Td>
                      <Badge tone={organization.is_active ? "success" : "neutral"}>
                        {organization.is_active ? "Active" : "Deactivated"}
                      </Badge>
                    </Td>
                    <Td className="hidden whitespace-nowrap md:table-cell">{formatDate(organization.created_at)}</Td>
                    <Td>
                      <div className="flex justify-end gap-0.5">
                        <button
                          type="button"
                          onClick={() => setAddingAdmin(organization)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                          aria-label={`Add an admin to ${organization.name}`}
                          title="Add admin"
                        >
                          <UserPlus className="size-4" aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditing(organization)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                          aria-label={`Edit ${organization.name}`}
                          title="Edit"
                        >
                          <Pencil className="size-4" aria-hidden="true" />
                        </button>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} size={data.size} total={data.total} onPageChange={(page) => update({ page })} />
          </>
        )}
      </Card>

      <p className="mt-4 text-xs text-slate-500">
        You see only names and counts. Factories, inspections, incidents, documents and conversations of an organization
        are visible to its own users only.
      </p>

      {creating && <CreateOrganizationDialog onClose={() => setCreating(false)} />}
      {editing && <EditOrganizationDialog organization={editing} onClose={() => setEditing(null)} />}
      {addingAdmin && <AddAdminDialog organization={addingAdmin} onClose={() => setAddingAdmin(null)} />}
    </>
  );
}

export function OrganizationsView() {
  const { isSuperAdmin } = useSession();
  if (!isSuperAdmin) {
    return (
      <>
        <PageHeader title="Organizations" />
        <Card>
          <EmptyState
            icon={<Lock className="size-5" aria-hidden="true" />}
            title="Only the platform administrator manages organizations"
          />
        </Card>
      </>
    );
  }
  return <OrganizationsList />;
}
