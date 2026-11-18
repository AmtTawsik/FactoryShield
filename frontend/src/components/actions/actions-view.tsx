"use client";

import { ListChecks, Plus, X } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, DetailList, PageHeader } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { FilterSelect } from "@/components/ui/form";
import { RowActions } from "@/components/ui/row-actions";
import { ExportButton, type CsvColumn } from "@/components/ui/export-button";
import { FilterBar, SearchInput } from "@/components/ui/search-input";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { api, errorMessage, withQuery } from "@/lib/api";
import { cn } from "@/lib/cn";
import { daysUntil, formatDate, formatDateTime, isoToLocalInput } from "@/lib/format";
import { ACTION_PRIORITY, ACTION_STATUS, ACTION_STATUS_TONE, OPTIONS, PRIORITY_TONE } from "@/lib/labels";
import type { ActionStatus, CorrectiveAction, Page } from "@/lib/types";
import { ActionFormDialog } from "./action-form";

const FILTERS = ["search", "factory_id", "status", "priority", "overdue", "inspection_id", "incident_id"] as const;

export function DueDate({ action }: { action: CorrectiveAction }) {
  const days = daysUntil(action.due_date);
  return (
    <div className="whitespace-nowrap">
      <p className={cn(action.is_overdue ? "font-medium text-red-700" : "text-slate-800")}>{formatDate(action.due_date)}</p>
      {action.status !== "completed" && (
        <p className={cn("text-xs", action.is_overdue ? "text-red-700" : days <= 3 ? "text-amber-700" : "text-slate-500")}>
          {action.is_overdue
            ? `Overdue by ${-days} day${days === -1 ? "" : "s"}`
            : days === 0
              ? "Due today"
              : `Due in ${days} day${days === 1 ? "" : "s"}`}
        </p>
      )}
    </div>
  );
}

function StatusSelect({ action, onChanged }: { action: CorrectiveAction; onChanged: () => Promise<unknown> }) {
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  async function change(status: ActionStatus) {
    setSaving(true);
    try {
      await api(`/corrective-actions/${action.id}`, { method: "PATCH", body: { status } });
      await onChanged();
      toast.success(`Marked as ${ACTION_STATUS[status].toLowerCase()}`);
    } catch (caught) {
      toast.error(errorMessage(caught));
    } finally {
      setSaving(false);
    }
  }

  return (
    <select
      aria-label={`Status of ${action.title}`}
      value={action.status}
      disabled={saving}
      onClick={(event) => event.stopPropagation()}
      onChange={(event) => change(event.target.value as ActionStatus)}
      className={cn(
        "h-8 rounded-md border bg-white px-2 pr-7 text-xs font-medium focus:ring-2 focus:ring-brand-500/20 focus:outline-none disabled:opacity-60",
        action.status === "completed"
          ? "border-green-200 text-green-700"
          : action.status === "in_progress"
            ? "border-brand-200 text-brand-700"
            : "border-slate-300 text-slate-700",
      )}
    >
      {OPTIONS.actionStatus.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

export function ActionsView() {
  const { isAdmin } = useSession();
  const factories = useAllFactories();
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const { data, error, isLoading, mutate } = useSWR<Page<CorrectiveAction>>(withQuery("/corrective-actions", values));
  const revalidate = useRevalidate();
  const toast = useToast();

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<CorrectiveAction | null>(null);
  const [deleting, setDeleting] = useState<CorrectiveAction | null>(null);
  const [viewing, setViewing] = useState<CorrectiveAction | null>(null);

  const csvColumns: CsvColumn<CorrectiveAction>[] = [
    { header: "Action", value: (a) => a.title },
    { header: "Factory", value: (a) => factories.nameOf(a.factory_id) },
    { header: "Responsible", value: (a) => a.assigned_to },
    { header: "Priority", value: (a) => ACTION_PRIORITY[a.priority] },
    { header: "Due date", value: (a) => a.due_date },
    { header: "Status", value: (a) => ACTION_STATUS[a.status] },
    { header: "Overdue", value: (a) => (a.is_overdue ? "Yes" : "No") },
    { header: "Completed (Bangladesh time)", value: (a) => a.completed_at && isoToLocalInput(a.completed_at).replace("T", " ") },
    { header: "Linked inspection ID", value: (a) => a.inspection_id },
    { header: "Linked incident ID", value: (a) => a.incident_id },
    { header: "Details", value: (a) => a.description },
  ];

  const linkFilter = values.inspection_id
    ? { label: `Inspection #${values.inspection_id}`, key: "inspection_id" as const }
    : values.incident_id
      ? { label: `Incident #${values.incident_id}`, key: "incident_id" as const }
      : null;

  return (
    <>
      <PageHeader
        title="Corrective actions"
        description="Fixes assigned after inspections and incidents, with owners and due dates."
        actions={
          <>
            <ExportButton path="/corrective-actions" filters={values} columns={csvColumns} fileName="corrective-actions" disabled={!data?.total} />
            {isAdmin && (
              <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
                New action
              </Button>
            )}
          </>
        }
      />

      <Card>
        <FilterBar activeCount={activeCount} onClear={clear}>
          <SearchInput
            value={values.search}
            onChange={(search) => update({ search })}
            placeholder="Search action or assignee"
            className="w-full sm:w-64"
          />
          <FilterSelect
            label="Factory"
            value={values.factory_id}
            onChange={(factory_id) => update({ factory_id })}
            options={factories.options}
            allLabel="All factories"
            className="w-full sm:w-56"
          />
          <FilterSelect
            label="Status"
            value={values.status}
            onChange={(status) => update({ status })}
            options={OPTIONS.actionStatus}
            allLabel="Any status"
            className="w-full sm:w-36"
          />
          <FilterSelect
            label="Priority"
            value={values.priority}
            onChange={(priority) => update({ priority })}
            options={OPTIONS.actionPriority}
            allLabel="Any priority"
            className="w-full sm:w-36"
          />
          <FilterSelect
            label="Due"
            value={values.overdue}
            onChange={(overdue) => update({ overdue })}
            options={[
              { value: "true", label: "Overdue only" },
              { value: "false", label: "Not overdue" },
            ]}
            allLabel="Any due date"
            className="w-full sm:w-40"
          />
          {linkFilter && (
            <span className="inline-flex h-9 items-center gap-1 rounded-md bg-brand-50 pr-1 pl-2.5 text-sm text-brand-800 ring-1 ring-brand-200 ring-inset">
              {linkFilter.label}
              <button
                type="button"
                onClick={() => update({ [linkFilter.key]: "" })}
                className="rounded p-1 hover:bg-brand-100"
                aria-label={`Remove filter ${linkFilter.label}`}
              >
                <X className="size-3.5" aria-hidden="true" />
              </button>
            </span>
          )}
        </FilterBar>

        {error ? (
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        ) : isLoading || !data ? (
          <TableSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={<ListChecks className="size-5" aria-hidden="true" />}
            title={activeCount ? "No corrective actions match these filters" : "No corrective actions yet"}
            description={activeCount ? "Try different filters or clear them." : "Actions created after inspections and incidents appear here."}
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Action</Th>
                <Th className="hidden md:table-cell">Factory</Th>
                <Th className="hidden sm:table-cell">Priority</Th>
                <Th>Due</Th>
                <Th>Status</Th>
                {isAdmin && <Th className="w-20"><span className="sr-only">Actions</span></Th>}
              </THead>
              <TBody>
                {data.items.map((action) => (
                  <Tr key={action.id} className="cursor-pointer" onClick={() => setViewing(action)}>
                    <Td className="max-w-sm">
                      <button
                        type="button"
                        className="text-left font-medium text-slate-900 hover:text-brand-700"
                        onClick={(event) => {
                          event.stopPropagation();
                          setViewing(action);
                        }}
                      >
                        {action.title}
                      </button>
                      <p className="truncate text-xs text-slate-500">{action.assigned_to}</p>
                    </Td>
                    <Td className="hidden max-w-52 truncate md:table-cell">{factories.nameOf(action.factory_id)}</Td>
                    <Td className="hidden sm:table-cell">
                      <Badge tone={PRIORITY_TONE[action.priority]}>{ACTION_PRIORITY[action.priority]}</Badge>
                    </Td>
                    <Td>
                      <DueDate action={action} />
                    </Td>
                    <Td>
                      {isAdmin ? (
                        <StatusSelect action={action} onChanged={() => revalidate("/corrective-actions")} />
                      ) : (
                        <Badge tone={ACTION_STATUS_TONE[action.status]}>{ACTION_STATUS[action.status]}</Badge>
                      )}
                    </Td>
                    {isAdmin && (
                      <Td>
                        <RowActions
                          label={action.title}
                          onEdit={() => setEditing(action)}
                          onDelete={() => setDeleting(action)}
                        />
                      </Td>
                    )}
                  </Tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} size={data.size} total={data.total} onPageChange={(page) => update({ page })} />
          </>
        )}
      </Card>

      {viewing && (
        <Dialog
          open
          onClose={() => setViewing(null)}
          title={viewing.title}
          description={factories.nameOf(viewing.factory_id)}
          footer={
            isAdmin && (
              <Button
                onClick={() => {
                  setEditing(viewing);
                  setViewing(null);
                }}
              >
                Edit
              </Button>
            )
          }
        >
          <DetailList
            items={[
              { label: "Responsible", value: viewing.assigned_to },
              { label: "Due", value: <DueDate action={viewing} /> },
              {
                label: "Priority",
                value: <Badge tone={PRIORITY_TONE[viewing.priority]}>{ACTION_PRIORITY[viewing.priority]}</Badge>,
              },
              {
                label: "Status",
                value: <Badge tone={ACTION_STATUS_TONE[viewing.status]}>{ACTION_STATUS[viewing.status]}</Badge>,
              },
              { label: "Completed", value: formatDateTime(viewing.completed_at) },
              {
                label: "Linked to",
                value:
                  [
                    viewing.inspection_id && `Inspection #${viewing.inspection_id}`,
                    viewing.incident_id && `Incident #${viewing.incident_id}`,
                  ]
                    .filter(Boolean)
                    .join(", ") || "—",
              },
            ]}
          />
          <div className="mt-5">
            <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Details</p>
            <p className="mt-1 text-sm whitespace-pre-line text-slate-800">{viewing.description || "No details added."}</p>
          </div>
        </Dialog>
      )}

      {creating && (
        <ActionFormDialog
          factoryId={values.factory_id ? Number(values.factory_id) : undefined}
          onClose={() => setCreating(false)}
        />
      )}
      {editing && <ActionFormDialog action={editing} onClose={() => setEditing(null)} />}
      <ConfirmDialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title="Delete corrective action?"
        description={
          deleting && (
            <>
              <strong>{deleting.title}</strong> will be removed. This cannot be undone.
            </>
          )
        }
        onConfirm={async () => {
          if (!deleting) return;
          await api(`/corrective-actions/${deleting.id}`, { method: "DELETE" });
          await revalidate("/corrective-actions");
          toast.success("Corrective action deleted");
        }}
      />
    </>
  );
}
