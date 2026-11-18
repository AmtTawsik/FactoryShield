"use client";

import { Plus, TriangleAlert } from "lucide-react";
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
import { FilterBar, SearchInput } from "@/components/ui/search-input";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { api, errorMessage, withQuery } from "@/lib/api";
import { formatDateTime, isoToLocalInput } from "@/lib/format";
import {
  INCIDENT_SEVERITY,
  INCIDENT_STATUS,
  INCIDENT_STATUS_TONE,
  INCIDENT_TYPE,
  OPTIONS,
  SEVERITY_TONE,
} from "@/lib/labels";
import type { Incident, Page } from "@/lib/types";
import { IncidentFormDialog } from "./incident-form";

const FILTERS = ["factory_id", "incident_type", "severity", "status", "search", "date_from", "date_to"] as const;

export function IncidentsView() {
  const { isAdmin } = useSession();
  const factories = useAllFactories();
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const { data, error, isLoading, mutate } = useSWR<Page<Incident>>(withQuery("/incidents", values));
  const revalidate = useRevalidate();
  const toast = useToast();

  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Incident | null>(null);
  const [deleting, setDeleting] = useState<Incident | null>(null);
  const [viewing, setViewing] = useState<Incident | null>(null);
  const [actionFor, setActionFor] = useState<Incident | null>(null);

  const csvColumns: CsvColumn<Incident>[] = [
    { header: "Occurred (Bangladesh time)", value: (i) => isoToLocalInput(i.occurred_at).replace("T", " ") },
    { header: "Factory", value: (i) => factories.nameOf(i.factory_id) },
    { header: "Type", value: (i) => INCIDENT_TYPE[i.incident_type] },
    { header: "Severity", value: (i) => INCIDENT_SEVERITY[i.severity] },
    { header: "Location", value: (i) => i.location },
    { header: "People injured", value: (i) => i.injured_count },
    { header: "Status", value: (i) => INCIDENT_STATUS[i.status] },
    { header: "Description", value: (i) => i.description },
  ];

  return (
    <>
      <PageHeader
        title="Incidents"
        description="Accidents, fires, near misses and other safety events."
        actions={
          <>
            <ExportButton path="/incidents" filters={values} columns={csvColumns} fileName="incidents" disabled={!data?.total} />
            {isAdmin && (
              <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
                Report incident
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
            placeholder="Search description or location"
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
            label="Type"
            value={values.incident_type}
            onChange={(incident_type) => update({ incident_type })}
            options={OPTIONS.incidentType}
            allLabel="All types"
            className="w-full sm:w-36"
          />
          <FilterSelect
            label="Severity"
            value={values.severity}
            onChange={(severity) => update({ severity })}
            options={OPTIONS.incidentSeverity}
            allLabel="Any severity"
            className="w-full sm:w-36"
          />
          <FilterSelect
            label="Status"
            value={values.status}
            onChange={(status) => update({ status })}
            options={OPTIONS.incidentStatus}
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
            icon={<TriangleAlert className="size-5" aria-hidden="true" />}
            title={activeCount ? "No incidents match these filters" : "No incidents reported"}
            description={activeCount ? "Try different filters or clear them." : "Reported incidents will appear here."}
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Occurred</Th>
                <Th className="hidden sm:table-cell">Factory</Th>
                <Th className="hidden sm:table-cell">Type</Th>
                <Th>Severity</Th>
                <Th className="hidden lg:table-cell">Location</Th>
                <Th className="hidden text-right md:table-cell">Injured</Th>
                <Th>Status</Th>
                {isAdmin && <Th className="w-20"><span className="sr-only">Actions</span></Th>}
              </THead>
              <TBody>
                {data.items.map((incident) => (
                  <Tr key={incident.id} className="cursor-pointer" onClick={() => setViewing(incident)}>
                    <Td className="whitespace-nowrap">
                      <button
                        type="button"
                        className="font-medium text-slate-900 hover:text-brand-700"
                        onClick={(event) => {
                          event.stopPropagation();
                          setViewing(incident);
                        }}
                      >
                        {formatDateTime(incident.occurred_at)}
                      </button>
                    </Td>
                    <Td className="hidden max-w-52 truncate sm:table-cell">{factories.nameOf(incident.factory_id)}</Td>
                    <Td className="hidden sm:table-cell">{INCIDENT_TYPE[incident.incident_type]}</Td>
                    <Td>
                      <Badge tone={SEVERITY_TONE[incident.severity]}>{INCIDENT_SEVERITY[incident.severity]}</Badge>
                    </Td>
                    <Td className="hidden max-w-48 truncate lg:table-cell">{incident.location}</Td>
                    <Td className="hidden text-right tabular-nums md:table-cell">{incident.injured_count}</Td>
                    <Td>
                      <Badge tone={INCIDENT_STATUS_TONE[incident.status]}>{INCIDENT_STATUS[incident.status]}</Badge>
                    </Td>
                    {isAdmin && (
                      <Td>
                        <RowActions
                          label={`incident on ${formatDateTime(incident.occurred_at)}`}
                          onEdit={() => setEditing(incident)}
                          onDelete={() => setDeleting(incident)}
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
          title={`${INCIDENT_TYPE[viewing.incident_type]} incident`}
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
              { label: "Occurred", value: formatDateTime(viewing.occurred_at) },
              {
                label: "Severity",
                value: <Badge tone={SEVERITY_TONE[viewing.severity]}>{INCIDENT_SEVERITY[viewing.severity]}</Badge>,
              },
              {
                label: "Status",
                value: <Badge tone={INCIDENT_STATUS_TONE[viewing.status]}>{INCIDENT_STATUS[viewing.status]}</Badge>,
              },
              { label: "Location", value: viewing.location },
              { label: "People injured", value: viewing.injured_count },
              { label: "Reported", value: formatDateTime(viewing.created_at) },
            ]}
          />
          <div className="mt-5">
            <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Description</p>
            <p className="mt-1 text-sm whitespace-pre-line text-slate-800">{viewing.description}</p>
          </div>
          <Link
            href={`/actions?factory_id=${viewing.factory_id}&incident_id=${viewing.id}`}
            className="mt-5 inline-block text-sm font-medium text-brand-700 hover:text-brand-800"
          >
            View corrective actions for this incident →
          </Link>
        </Dialog>
      )}

      {creating && <IncidentFormDialog onClose={() => setCreating(false)} />}
      {editing && <IncidentFormDialog incident={editing} onClose={() => setEditing(null)} />}
      {actionFor && (
        <ActionFormDialog factoryId={actionFor.factory_id} incidentId={actionFor.id} onClose={() => setActionFor(null)} />
      )}
      <ConfirmDialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title="Delete incident?"
        description={
          deleting && (
            <>
              The {INCIDENT_TYPE[deleting.incident_type].toLowerCase()} incident at{" "}
              <strong>{factories.nameOf(deleting.factory_id)}</strong> ({formatDateTime(deleting.occurred_at)}) will be
              removed. Linked corrective actions are kept but no longer linked. This cannot be undone.
            </>
          )
        }
        onConfirm={async () => {
          if (!deleting) return;
          await api(`/incidents/${deleting.id}`, { method: "DELETE" });
          await revalidate("/incidents", "/corrective-actions");
          toast.success("Incident deleted");
        }}
      />
    </>
  );
}
