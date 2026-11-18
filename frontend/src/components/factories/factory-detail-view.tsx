"use client";

import { ArrowLeft, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import useSWR from "swr";
import { ActionFormDialog } from "@/components/actions/action-form";
import { DueDate } from "@/components/actions/actions-view";
import { IncidentFormDialog } from "@/components/incidents/incident-form";
import { InspectionFormDialog } from "@/components/inspections/inspection-form";
import { ScoreBadge } from "@/components/inspections/inspections-view";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, DetailList, PageHeader } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState, ErrorState, LoadingBlock, TableSkeleton } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { useRevalidate } from "@/hooks/use-revalidate";
import { ApiError, api, errorMessage } from "@/lib/api";
import { formatDate, formatDateTime, formatNumber } from "@/lib/format";
import {
  ACTION_PRIORITY,
  ACTION_STATUS,
  ACTION_STATUS_TONE,
  INCIDENT_SEVERITY,
  INCIDENT_STATUS,
  INCIDENT_STATUS_TONE,
  INCIDENT_TYPE,
  INSPECTION_CATEGORY,
  INSPECTION_STATUS,
  INSPECTION_STATUS_TONE,
  PRIORITY_TONE,
  SEVERITY_TONE,
  scoreTone,
  type Tone,
} from "@/lib/labels";
import type { CorrectiveAction, DashboardSummary, Factory, Incident, Inspection, Page } from "@/lib/types";
import { FactoryFormDialog } from "./factory-form";

const RECENT = 5;

function Section<T>({
  title,
  viewAllHref,
  addLabel,
  onAdd,
  data,
  error,
  retry,
  emptyText,
  head,
  row,
}: {
  title: string;
  viewAllHref: string;
  addLabel?: string;
  onAdd?: () => void;
  data?: Page<T>;
  error?: unknown;
  retry: () => void;
  emptyText: string;
  head: ReactNode;
  row: (item: T) => ReactNode;
}) {
  return (
    <Card>
      <CardHeader
        title={title}
        description={data ? `${data.total} in total` : undefined}
        action={
          <div className="flex items-center gap-2">
            {onAdd && (
              <Button variant="secondary" size="sm" icon={<Plus className="size-3.5" aria-hidden="true" />} onClick={onAdd}>
                {addLabel}
              </Button>
            )}
            <Link href={viewAllHref} className="text-sm font-medium text-brand-700 hover:text-brand-800">
              View all →
            </Link>
          </div>
        }
      />
      {error ? (
        <ErrorState message={errorMessage(error)} onRetry={retry} />
      ) : !data ? (
        <TableSkeleton rows={3} />
      ) : data.items.length === 0 ? (
        <EmptyState title={emptyText} className="py-8" />
      ) : (
        <Table>
          <THead>{head}</THead>
          <TBody>{data.items.map(row)}</TBody>
        </Table>
      )}
    </Card>
  );
}

const STAT_COLOR: Record<Tone, string> = {
  neutral: "text-slate-900",
  brand: "text-brand-700",
  success: "text-green-700",
  warning: "text-amber-700",
  danger: "text-red-700",
};

function Stat({ label, value, tone = "neutral" }: { label: string; value: string; tone?: Tone }) {
  const color = STAT_COLOR[tone];
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

export function FactoryDetailView() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const router = useRouter();
  const { isAdmin } = useSession();
  const revalidate = useRevalidate();
  const toast = useToast();

  const validId = Number.isInteger(id) && id > 0;
  const { data: factory, error, mutate } = useSWR<Factory>(validId ? `/factories/${id}` : null);
  const ready = Boolean(factory);
  const summary = useSWR<DashboardSummary>(ready ? `/dashboard/summary?factory_id=${id}` : null);
  const inspections = useSWR<Page<Inspection>>(ready ? `/inspections?factory_id=${id}&size=${RECENT}` : null);
  const incidents = useSWR<Page<Incident>>(ready ? `/incidents?factory_id=${id}&size=${RECENT}` : null);
  const overdue = useSWR<Page<CorrectiveAction>>(ready ? `/corrective-actions?factory_id=${id}&overdue=true&size=1` : null);
  const actions = useSWR<Page<CorrectiveAction>>(ready ? `/corrective-actions?factory_id=${id}&size=${RECENT}` : null);

  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [adding, setAdding] = useState<"inspection" | "incident" | "action" | null>(null);

  const back = (
    <Link href="/factories" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden="true" /> Factories
    </Link>
  );

  if (!validId || (error instanceof ApiError && error.status === 404)) {
    return (
      <>
        <PageHeader title="Factory not found" breadcrumb={back} />
        <Card>
          <EmptyState
            title="This factory does not exist or is not assigned to you"
            action={
              <Link href="/factories" className="text-sm font-medium text-brand-700">
                Back to factories
              </Link>
            }
          />
        </Card>
      </>
    );
  }
  if (error) {
    return (
      <>
        <PageHeader title="Factory" breadcrumb={back} />
        <Card>
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        </Card>
      </>
    );
  }
  if (!factory) return <LoadingBlock label="Loading factory…" />;

  const totals = summary.data;
  const overdueCount = overdue.data?.total;

  return (
    <>
      <PageHeader
        breadcrumb={back}
        title={
          <span className="flex flex-wrap items-center gap-2">
            {factory.name}
            <Badge tone={factory.is_active ? "success" : "neutral"}>{factory.is_active ? "Active" : "Inactive"}</Badge>
          </span>
        }
        description={factory.address.toLowerCase().includes(factory.district.toLowerCase()) ? factory.address : `${factory.address}, ${factory.district}`}
        actions={
          isAdmin && (
            <>
              <Button variant="secondary" icon={<Pencil className="size-4" aria-hidden="true" />} onClick={() => setEditing(true)}>
                Edit
              </Button>
              <Button variant="secondary" icon={<Trash2 className="size-4" aria-hidden="true" />} onClick={() => setDeleting(true)} className="text-red-700 hover:bg-red-50">
                Delete
              </Button>
            </>
          )
        }
      />

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat
            label="Average score (90 days)"
            value={totals?.inspections.average_score_last_90_days?.toFixed(1) ?? "—"}
            tone={scoreTone(totals?.inspections.average_score_last_90_days)}
          />
          <Stat label="Upcoming inspections" value={totals ? String(totals.inspections.scheduled_upcoming) : "—"} />
          <Stat
            label="Open incidents"
            value={totals ? String(totals.incidents.not_closed) : "—"}
            tone={totals && totals.incidents.serious_not_closed > 0 ? "danger" : undefined}
          />
          <Stat
            label="Overdue actions"
            value={overdueCount === undefined ? "—" : String(overdueCount)}
            tone={overdueCount ? "danger" : overdueCount === 0 ? "success" : undefined}
          />
        </div>

        <Card>
          <CardHeader title="Factory details" />
          <div className="p-4">
            <DetailList
              items={[
                { label: "Licence number", value: <span className="font-mono">{factory.license_number}</span> },
                { label: "District", value: factory.district },
                { label: "Address", value: factory.address },
                { label: "Workers", value: formatNumber(factory.worker_count) },
                { label: "Floors", value: factory.floor_count },
                { label: "Contact person", value: factory.contact_person },
                { label: "Contact mobile", value: <a href={`tel:${factory.contact_phone}`} className="text-brand-700 hover:underline">{factory.contact_phone}</a> },
                { label: "Registered", value: formatDate(factory.created_at) },
                { label: "Last updated", value: formatDateTime(factory.updated_at) },
              ]}
            />
          </div>
        </Card>

        <Section
          title="Recent inspections"
          viewAllHref={`/inspections?factory_id=${id}`}
          addLabel="New inspection"
          onAdd={isAdmin ? () => setAdding("inspection") : undefined}
          data={inspections.data}
          error={inspections.error}
          retry={() => inspections.mutate()}
          emptyText="No inspections recorded for this factory"
          head={
            <>
              <Th>Date</Th>
              <Th>Category</Th>
              <Th>Status</Th>
              <Th className="text-right">Score</Th>
              <Th className="hidden md:table-cell">Findings</Th>
            </>
          }
          row={(item) => (
            <Tr key={item.id}>
              <Td className="whitespace-nowrap">{formatDate(item.inspection_date)}</Td>
              <Td>{INSPECTION_CATEGORY[item.category]}</Td>
              <Td>
                <Badge tone={INSPECTION_STATUS_TONE[item.status]}>{INSPECTION_STATUS[item.status]}</Badge>
              </Td>
              <Td className="text-right">
                <ScoreBadge score={item.score} />
              </Td>
              <Td className="hidden max-w-md truncate text-slate-500 md:table-cell">{item.findings ?? "—"}</Td>
            </Tr>
          )}
        />

        <Section
          title="Recent incidents"
          viewAllHref={`/incidents?factory_id=${id}`}
          addLabel="Report incident"
          onAdd={isAdmin ? () => setAdding("incident") : undefined}
          data={incidents.data}
          error={incidents.error}
          retry={() => incidents.mutate()}
          emptyText="No incidents reported for this factory"
          head={
            <>
              <Th>Occurred</Th>
              <Th>Type</Th>
              <Th>Severity</Th>
              <Th className="hidden md:table-cell">Location</Th>
              <Th>Status</Th>
            </>
          }
          row={(item) => (
            <Tr key={item.id}>
              <Td className="whitespace-nowrap">{formatDateTime(item.occurred_at)}</Td>
              <Td>{INCIDENT_TYPE[item.incident_type]}</Td>
              <Td>
                <Badge tone={SEVERITY_TONE[item.severity]}>{INCIDENT_SEVERITY[item.severity]}</Badge>
              </Td>
              <Td className="hidden max-w-xs truncate md:table-cell">{item.location}</Td>
              <Td>
                <Badge tone={INCIDENT_STATUS_TONE[item.status]}>{INCIDENT_STATUS[item.status]}</Badge>
              </Td>
            </Tr>
          )}
        />

        <Section
          title="Corrective actions"
          viewAllHref={`/actions?factory_id=${id}`}
          addLabel="New action"
          onAdd={isAdmin ? () => setAdding("action") : undefined}
          data={actions.data}
          error={actions.error}
          retry={() => actions.mutate()}
          emptyText="No corrective actions for this factory"
          head={
            <>
              <Th>Action</Th>
              <Th>Priority</Th>
              <Th>Due</Th>
              <Th>Status</Th>
            </>
          }
          row={(item) => (
            <Tr key={item.id}>
              <Td className="max-w-sm">
                <p className="font-medium text-slate-900">{item.title}</p>
                <p className="truncate text-xs text-slate-500">{item.assigned_to}</p>
              </Td>
              <Td>
                <Badge tone={PRIORITY_TONE[item.priority]}>{ACTION_PRIORITY[item.priority]}</Badge>
              </Td>
              <Td>
                <DueDate action={item} />
              </Td>
              <Td>
                <Badge tone={ACTION_STATUS_TONE[item.status]}>{ACTION_STATUS[item.status]}</Badge>
              </Td>
            </Tr>
          )}
        />
      </div>

      {editing && <FactoryFormDialog factory={factory} onClose={() => setEditing(false)} />}
      {adding === "inspection" && <InspectionFormDialog factoryId={id} onClose={() => setAdding(null)} />}
      {adding === "incident" && <IncidentFormDialog factoryId={id} onClose={() => setAdding(null)} />}
      {adding === "action" && <ActionFormDialog factoryId={id} onClose={() => setAdding(null)} />}
      <ConfirmDialog
        open={deleting}
        onClose={() => setDeleting(false)}
        title="Delete factory?"
        confirmLabel="Delete factory"
        description={
          <>
            <strong>{factory.name}</strong> and all of its inspections, incidents, corrective actions, documents and
            assistant conversations will be permanently deleted. To keep the history, edit the factory and mark it
            inactive instead.
          </>
        }
        onConfirm={async () => {
          await api(`/factories/${id}`, { method: "DELETE" });
          toast.success(`${factory.name} deleted`);
          router.replace("/factories");
          await revalidate("/factories", "/inspections", "/incidents", "/corrective-actions");
        }}
      />
    </>
  );
}
