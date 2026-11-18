"use client";

import { ArrowRight, Building2, ClipboardCheck, ListChecks, TriangleAlert } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import useSWR from "swr";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, PageHeader } from "@/components/ui/card";
import { FilterSelect } from "@/components/ui/form";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { useAllFactories } from "@/hooks/use-factories";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { errorMessage, withQuery } from "@/lib/api";
import { cn } from "@/lib/cn";
import { daysUntil, formatDate, formatNumber } from "@/lib/format";
import { INSPECTION_CATEGORY, scoreTone, type Tone } from "@/lib/labels";
import type { DashboardSummary } from "@/lib/types";
import { ScoreTrendChart, SeverityChart } from "./charts";

const FILTERS = ["factory_id"] as const;

const TONE_TEXT: Record<Tone, string> = {
  neutral: "text-slate-900",
  brand: "text-brand-700",
  success: "text-green-700",
  warning: "text-amber-700",
  danger: "text-red-700",
};

function StatTile({
  label,
  value,
  detail,
  icon,
  href,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail: ReactNode;
  icon: ReactNode;
  href: string;
  tone?: Tone;
}) {
  return (
    <Link
      href={href}
      className="group rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-brand-300"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span className="text-slate-400 group-hover:text-brand-600">{icon}</span>
      </div>
      <p className={cn("mt-2 text-2xl font-semibold tracking-tight tabular-nums", TONE_TEXT[tone])}>{value}</p>
      <p className="mt-1 text-sm text-slate-500">{detail}</p>
    </Link>
  );
}

function DashboardSkeleton() {
  return (
    <div role="status" aria-label="Loading dashboard" className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((key) => (
          <div key={key} className="rounded-lg border border-slate-200 bg-white p-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="mt-3 h-7 w-16" />
            <Skeleton className="mt-2 h-4 w-32" />
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-80 lg:col-span-2" />
        <Skeleton className="h-80" />
      </div>
    </div>
  );
}

export function DashboardView() {
  const { values, update } = useUrlFilters(FILTERS);
  const factories = useAllFactories();
  const { data, error, isLoading, mutate } = useSWR<DashboardSummary>(
    withQuery("/dashboard/summary", { factory_id: values.factory_id }),
  );

  const factoryQuery = values.factory_id ? `factory_id=${values.factory_id}&` : "";

  return (
    <>
      <PageHeader
        title="Dashboard"
        description={data ? `Safety overview as of ${formatDate(data.as_of)}` : "Safety overview"}
        actions={
          factories.factories.length > 1 && (
            <FilterSelect
              label="Factory"
              value={values.factory_id}
              onChange={(factory_id) => update({ factory_id })}
              options={factories.options}
              allLabel="All factories"
              className="w-64 max-w-full"
            />
          )
        }
      />

      {error ? (
        <Card>
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        </Card>
      ) : isLoading || !data ? (
        <DashboardSkeleton />
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatTile
              label="Active factories"
              value={formatNumber(data.factories)}
              detail={`${formatNumber(data.workers)} workers`}
              icon={<Building2 className="size-4" aria-hidden="true" />}
              href="/factories"
            />
            <StatTile
              label="Average inspection score"
              value={data.inspections.average_score_last_90_days?.toFixed(1) ?? "—"}
              detail={`${data.inspections.completed_last_90_days} completed in the last 90 days`}
              icon={<ClipboardCheck className="size-4" aria-hidden="true" />}
              href={`/inspections?${factoryQuery}status=completed`}
              tone={scoreTone(data.inspections.average_score_last_90_days)}
            />
            <StatTile
              label="Open incidents"
              value={formatNumber(data.incidents.not_closed)}
              detail={
                data.incidents.serious_not_closed > 0 ? (
                  <span className="text-red-700">{data.incidents.serious_not_closed} high or critical</span>
                ) : (
                  "None high or critical"
                )
              }
              icon={<TriangleAlert className="size-4" aria-hidden="true" />}
              href={`/incidents?${factoryQuery}`}
              tone={data.incidents.serious_not_closed > 0 ? "danger" : "neutral"}
            />
            <StatTile
              label="Overdue actions"
              value={formatNumber(data.actions.overdue)}
              detail={`${data.actions.not_completed} not completed`}
              icon={<ListChecks className="size-4" aria-hidden="true" />}
              href={`/actions?${factoryQuery}overdue=true`}
              tone={data.actions.overdue > 0 ? "danger" : "success"}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader title="Inspection score trend" description="Average score of completed inspections, last 6 months" />
              <div className="p-4">
                {data.score_trend.some((row) => row.inspections > 0) ? (
                  <ScoreTrendChart data={data.score_trend} />
                ) : (
                  <EmptyState title="No completed inspections yet" description="Scores appear here once inspections are completed." />
                )}
              </div>
            </Card>
            <Card>
              <CardHeader title="Incidents by severity" description="Last 90 days" />
              <div className="p-4">
                {data.incidents_by_severity.some((row) => row.count > 0) ? (
                  <SeverityChart data={data.incidents_by_severity} />
                ) : (
                  <EmptyState title="No incidents in the last 90 days" />
                )}
              </div>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader
                title="Overdue actions by factory"
                description="Factories with the most overdue corrective actions"
                action={
                  <Link
                    href={`/actions?${factoryQuery}overdue=true`}
                    className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-800"
                  >
                    View all <ArrowRight className="size-3.5" aria-hidden="true" />
                  </Link>
                }
              />
              {data.overdue_by_factory.length === 0 ? (
                <EmptyState title="No overdue actions" description="Every open corrective action is within its due date." />
              ) : (
                <ul className="divide-y divide-slate-100">
                  {data.overdue_by_factory.map((row) => {
                    const max = data.overdue_by_factory[0].overdue;
                    return (
                      <li key={row.factory_id} className="px-4 py-3">
                        <div className="flex items-center justify-between gap-4 text-sm">
                          <Link
                            href={`/actions?factory_id=${row.factory_id}&overdue=true`}
                            className="truncate font-medium text-slate-800 hover:text-brand-700"
                          >
                            {row.factory_name}
                          </Link>
                          <span className="shrink-0 font-medium text-red-700 tabular-nums">{row.overdue} overdue</span>
                        </div>
                        <div className="mt-2 h-1.5 rounded-full bg-slate-100" aria-hidden="true">
                          <div className="h-1.5 rounded-full bg-red-500" style={{ width: `${(row.overdue / max) * 100}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </Card>

            <Card>
              <CardHeader
                title="Upcoming inspections"
                description={`${data.inspections.scheduled_upcoming} scheduled`}
                action={
                  <Link
                    href={`/inspections?${factoryQuery}status=scheduled`}
                    className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-800"
                  >
                    View all <ArrowRight className="size-3.5" aria-hidden="true" />
                  </Link>
                }
              />
              {data.upcoming_inspections.length === 0 ? (
                <EmptyState title="No inspections scheduled" />
              ) : (
                <ul className="divide-y divide-slate-100">
                  {data.upcoming_inspections.map((row) => {
                    const days = daysUntil(row.inspection_date);
                    return (
                      <li key={row.id} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
                        <div className="min-w-0">
                          <Link
                            href={`/factories/${row.factory_id}`}
                            className="block truncate font-medium text-slate-800 hover:text-brand-700"
                          >
                            {row.factory_name}
                          </Link>
                          <p className="text-slate-500">{INSPECTION_CATEGORY[row.category]}</p>
                        </div>
                        <div className="shrink-0 text-right">
                          <p className="text-slate-800">{formatDate(row.inspection_date)}</p>
                          <Badge tone={days <= 7 ? "warning" : "neutral"}>
                            {days === 0 ? "Today" : days === 1 ? "Tomorrow" : `In ${days} days`}
                          </Badge>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
