"use client";

import { ClipboardCheck, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { ActionFormDialog } from "@/components/actions/action-form";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, DetailList, PageHeader } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { FilterSelect } from "@/components/ui/form";
import { DateFilter, RowActions } from "@/components/ui/row-actions";
import { ExportButton, type CsvColumn } from "@/components/ui/export-button";
import { FilterBar } from "@/components/ui/search-input";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { api, errorMessage, withQuery } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/format";
import { INSPECTION_CATEGORY, INSPECTION_STATUS, INSPECTION_STATUS_TONE, OPTIONS, scoreTone } from "@/lib/labels";
import type { Inspection, Page, UserDetail } from "@/lib/types";
import { InspectionFormDialog } from "./inspection-form";

const FILTERS = ["factory_id", "category", "status", "date_from", "date_to"] as const;

export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-slate-400">—</span>;
  return (
    <Badge tone={scoreTone(score)} className="tabular-nums">
      {score}
    </Badge>
  );
}

function useInspectorNames(enabled: boolean) {
  const { data } = useSWR<Page<UserDetail>>(enabled ? "/users?size=100" : null);
  const names = new Map((data?.items ?? []).map((user) => [user.id, user.full_name]));
  return (id: number | null) => (id === null ? "Not assigned" : (names.get(id) ?? `User #${id}`));
}

export function InspectionsView() {
  const { isAdmin } = useSession();
  const factories = useAllFactories();
  const inspectorName = useInspectorNames(isAdmin);
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const { data, error, isLoading, mutate } = useSWR<Page<Inspection>>(withQuery("/inspections", values));
  const revalidate = useRevalidate();
  const toast = useToast();

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Inspection | null>(null);
  const [deleting, setDeleting] = useState<Inspection | null>(null);
  const [viewing, setViewing] = useState<Inspection | null>(null);
  const [actionFor, setActionFor] = useState<Inspection | null>(null);

  const csvColumns: CsvColumn<Inspection>[] = [
    { header: "Date", value: (i) => i.inspection_date },
    { header: "Factory", value: (i) => factories.nameOf(i.factory_id) },
    { header: "Category", value: (i) => INSPECTION_CATEGORY[i.category] },
    { header: "Status", value: (i) => INSPECTION_STATUS[i.status] },
    { header: "Score", value: (i) => i.score },
    ...(isAdmin ? [{ header: "Inspector", value: (i: Inspection) => inspectorName(i.inspector_id) }] : []),
    { header: "Findings", value: (i) => i.findings },
  ];

  return (
    <>
      <PageHeader
        title="Safety inspections"
        description="Scheduled and completed inspections with their scores and findings."
        actions={
          <>
            <ExportButton path="/inspections" filters={values} columns={csvColumns} fileName="inspections" disabled={!data?.total} />
            {isAdmin && (
              <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
                New inspection
              </Button>
            )}
          </>
        }
      />

      <Card>
        <FilterBar activeCount={activeCount} onClear={clear}>
          <FilterSelect
            label="Factory"
            value={values.factory_id}
            onChange={(factory_id) => update({ factory_id })}
            options={factories.options}
            allLabel="All factories"
            className="w-full sm:w-60"
          />
          <FilterSelect
            label="Category"
            value={values.category}
            onChange={(category) => update({ category })}
            options={OPTIONS.inspectionCategory}
            allLabel="All categories"
            className="w-full sm:w-40"
          />
          <FilterSelect
            label="Status"
            value={values.status}
            onChange={(status) => update({ status })}
            options={OPTIONS.inspectionStatus}
            allLabel="Any status"
            className="w-full sm:w-36"
          />
          <DateFilter label="From" value={values.date_from} onChange={(date_from) => update({ date_from })} />
          <DateFilter label="To" value={values.date_to} onChange={(date_to) => update({ date_to })} />
        </FilterBar>

        {error ? (
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        ) : isLoading || !data ? (
          <TableSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={<ClipboardCheck className="size-5" aria-hidden="true" />}
            title={activeCount ? "No inspections match these filters" : "No inspections yet"}
            description={activeCount ? "Try different filters or clear them." : "Scheduled and completed inspections will appear here."}
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Date</Th>
                <Th className="hidden sm:table-cell">Factory</Th>
                <Th>Category</Th>
                <Th>Status</Th>
                <Th className="text-right">Score</Th>
                {isAdmin && <Th className="hidden xl:table-cell">Inspector</Th>}
                <Th className="hidden lg:table-cell">Findings</Th>
                {isAdmin && <Th className="w-20"><span className="sr-only">Actions</span></Th>}
              </THead>
              <TBody>
                {data.items.map((inspection) => (
                  <Tr key={inspection.id} className="cursor-pointer" onClick={() => setViewing(inspection)}>
                    <Td className="whitespace-nowrap">
                      <button
                        type="button"
                        className="font-medium text-slate-900 hover:text-brand-700"
                        onClick={(event) => {
                          event.stopPropagation();
                          setViewing(inspection);
                        }}
                      >
                        {formatDate(inspection.inspection_date)}
                      </button>
                    </Td>
                    <Td className="hidden max-w-56 truncate sm:table-cell">{factories.nameOf(inspection.factory_id)}</Td>
                    <Td>{INSPECTION_CATEGORY[inspection.category]}</Td>
                    <Td>
                      <Badge tone={INSPECTION_STATUS_TONE[inspection.status]}>{INSPECTION_STATUS[inspection.status]}</Badge>
                    </Td>
                    <Td className="text-right">
                      <ScoreBadge score={inspection.score} />
                    </Td>
                    {isAdmin && <Td className="hidden xl:table-cell">{inspectorName(inspection.inspector_id)}</Td>}
                    <Td className="hidden max-w-xs truncate text-slate-500 lg:table-cell">{inspection.findings ?? "—"}</Td>
                    {isAdmin && (
                      <Td>
                        <RowActions
                          label={`inspection on ${formatDate(inspection.inspection_date)}`}
                          onEdit={() => setEditing(inspection)}
                          onDelete={() => setDeleting(inspection)}
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
          title={`${INSPECTION_CATEGORY[viewing.category]} inspection`}
          description={factories.nameOf(viewing.factory_id)}
          footer={
            isAdmin && (
              <>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setActionFor(viewing);
                    setViewing(null);
                  }}
                >
                  Add corrective action
                </Button>
                <Button
                  onClick={() => {
                    setEditing(viewing);
                    setViewing(null);
                  }}
                >
                  Edit
                </Button>
              </>
            )
          }
        >
          <DetailList
            items={[
              { label: "Date", value: formatDate(viewing.inspection_date) },
              {
                label: "Status",
                value: <Badge tone={INSPECTION_STATUS_TONE[viewing.status]}>{INSPECTION_STATUS[viewing.status]}</Badge>,
              },
              { label: "Score", value: <ScoreBadge score={viewing.score} /> },
              ...(isAdmin ? [{ label: "Inspector", value: inspectorName(viewing.inspector_id) }] : []),
              { label: "Last updated", value: formatDateTime(viewing.updated_at) },
            ]}
          />
          <div className="mt-5">
            <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Findings</p>
            <p className="mt-1 text-sm whitespace-pre-line text-slate-800">{viewing.findings || "No findings recorded."}</p>
          </div>
          <Link
            href={`/actions?factory_id=${viewing.factory_id}&inspection_id=${viewing.id}`}
            className="mt-5 inline-block text-sm font-medium text-brand-700 hover:text-brand-800"
          >
            View corrective actions for this inspection →
          </Link>
        </Dialog>
      )}

      {creating && <InspectionFormDialog onClose={() => setCreating(false)} />}
      {editing && <InspectionFormDialog inspection={editing} onClose={() => setEditing(null)} />}
      {actionFor && (
        <ActionFormDialog factoryId={actionFor.factory_id} inspectionId={actionFor.id} onClose={() => setActionFor(null)} />
      )}
      <ConfirmDialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title="Delete inspection?"
        description={
          deleting && (
            <>
              The {INSPECTION_CATEGORY[deleting.category].toLowerCase()} inspection of{" "}
              <strong>{factories.nameOf(deleting.factory_id)}</strong> on {formatDate(deleting.inspection_date)} will be
              removed. Linked corrective actions are kept but no longer linked. This cannot be undone.
            </>
          )
        }
        onConfirm={async () => {
          if (!deleting) return;
          await api(`/inspections/${deleting.id}`, { method: "DELETE" });
          await revalidate("/inspections", "/corrective-actions");
          toast.success("Inspection deleted");
        }}
      />
    </>
  );
}
