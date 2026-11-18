"use client";

import { Building2, Lock, Pencil, Plus, Users } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, PageHeader } from "@/components/ui/card";
import { FilterSelect } from "@/components/ui/form";
import { FilterBar, SearchInput } from "@/components/ui/search-input";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useAllFactories } from "@/hooks/use-factories";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { errorMessage, withQuery } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { OPTIONS, USER_ROLE } from "@/lib/labels";
import type { Page, UserDetail } from "@/lib/types";
import { CreateUserDialog, EditUserDialog, FactoriesDialog } from "./user-dialogs";

const FILTERS = ["search", "role", "is_active"] as const;

function FactoryAccess({ user }: { user: UserDetail }) {
  const factories = useAllFactories();
  if (user.role === "admin") return <span className="text-slate-500">All factories</span>;
  if (user.factory_ids.length === 0) return <span className="text-amber-700">None assigned</span>;
  const names = user.factory_ids.map((id) => factories.nameOf(id));
  return (
    <span title={names.join(", ")}>
      {names[0]}
      {names.length > 1 && <span className="text-slate-500"> +{names.length - 1} more</span>}
    </span>
  );
}

function UsersList() {
  const { user: me } = useSession();
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const { data, error, isLoading, mutate } = useSWR<Page<UserDetail>>(withQuery("/users", values));
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<UserDetail | null>(null);
  const [assigning, setAssigning] = useState<UserDetail | null>(null);

  return (
    <>
      <PageHeader
        title="User management"
        description="Accounts, roles and which factories each staff member can see."
        actions={
          <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
            Add user
          </Button>
        }
      />

      <Card>
        <FilterBar activeCount={activeCount} onClear={clear}>
          <SearchInput
            value={values.search}
            onChange={(search) => update({ search })}
            placeholder="Search name or email"
            className="w-full sm:w-64"
          />
          <FilterSelect
            label="Role"
            value={values.role}
            onChange={(role) => update({ role })}
            options={OPTIONS.userRole}
            allLabel="All roles"
            className="w-full sm:w-36"
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
            className="w-full sm:w-36"
          />
        </FilterBar>

        {error ? (
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        ) : isLoading || !data ? (
          <TableSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={<Users className="size-5" aria-hidden="true" />}
            title="No users match these filters"
            description="Try a different search or clear the filters."
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>User</Th>
                <Th>Role</Th>
                <Th className="hidden md:table-cell">Factory access</Th>
                <Th>Status</Th>
                <Th className="hidden lg:table-cell">Added</Th>
                <Th className="w-24">
                  <span className="sr-only">Actions</span>
                </Th>
              </THead>
              <TBody>
                {data.items.map((user) => (
                  <Tr key={user.id}>
                    <Td>
                      <p className="font-medium text-slate-900">
                        {user.full_name}
                        {user.id === me.id && <span className="ml-1.5 text-xs font-normal text-slate-500">(you)</span>}
                      </p>
                      <p className="text-xs text-slate-500">{user.email}</p>
                    </Td>
                    <Td>
                      <Badge tone={user.role === "admin" ? "brand" : "neutral"}>{USER_ROLE[user.role]}</Badge>
                    </Td>
                    <Td className="hidden max-w-60 truncate md:table-cell">
                      <FactoryAccess user={user} />
                    </Td>
                    <Td>
                      <Badge tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Active" : "Deactivated"}</Badge>
                    </Td>
                    <Td className="hidden whitespace-nowrap lg:table-cell">{formatDate(user.created_at)}</Td>
                    <Td>
                      <div className="flex justify-end gap-0.5">
                        <button
                          type="button"
                          onClick={() => setAssigning(user)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                          aria-label={`Assign factories to ${user.full_name}`}
                          title="Assign factories"
                        >
                          <Building2 className="size-4" aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditing(user)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                          aria-label={`Edit ${user.full_name}`}
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

      {creating && <CreateUserDialog onClose={() => setCreating(false)} />}
      {editing && <EditUserDialog user={editing} isSelf={editing.id === me.id} onClose={() => setEditing(null)} />}
      {assigning && <FactoriesDialog user={assigning} onClose={() => setAssigning(null)} />}
    </>
  );
}

export function UsersView() {
  const { isAdmin } = useSession();
  if (!isAdmin) {
    return (
      <>
        <PageHeader title="User management" />
        <Card>
          <EmptyState
            icon={<Lock className="size-5" aria-hidden="true" />}
            title="Only administrators can manage users"
            description="Ask an administrator if you need access to another factory."
          />
        </Card>
      </>
    );
  }
  return <UsersList />;
}
