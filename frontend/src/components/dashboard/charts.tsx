"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";
import { formatMonth } from "@/lib/format";
import { INCIDENT_SEVERITY } from "@/lib/labels";
import type { DashboardSummary } from "@/lib/types";

const AXIS = { fontSize: 12, fill: "#64748b" };
const GRID = "#e2e8f0";

const SEVERITY_COLOR = {
  low: "#94a3b8",
  medium: "#d97706",
  high: "#dc2626",
  critical: "#991b1b",
} as const;

function TooltipBox({ title, lines }: { title: string; lines: string[] }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="font-medium text-slate-900">{title}</p>
      {lines.map((line) => (
        <p key={line} className="mt-0.5 text-slate-600">
          {line}
        </p>
      ))}
    </div>
  );
}

type TrendRow = DashboardSummary["score_trend"][number];

function TrendTooltip({ active, payload }: TooltipContentProps) {
  const row = payload?.[0]?.payload as TrendRow | undefined;
  if (!active || !row) return null;
  return (
    <TooltipBox
      title={formatMonth(row.month)}
      lines={
        row.inspections
          ? [`Average score: ${row.average_score}`, `${row.inspections} completed inspection${row.inspections === 1 ? "" : "s"}`]
          : ["No completed inspections"]
      }
    />
  );
}

export function ScoreTrendChart({ data }: { data: DashboardSummary["score_trend"] }) {
  const summary = data
    .map((row) => `${formatMonth(row.month)}: ${row.average_score ?? "no inspections"}`)
    .join("; ");

  return (
    <figure className="h-64" aria-label={`Average inspection score by month. ${summary}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="month" tickFormatter={formatMonth} tick={AXIS} tickLine={false} axisLine={{ stroke: GRID }} />
          <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={AXIS} tickLine={false} axisLine={false} />
          <Tooltip content={TrendTooltip} cursor={{ stroke: "#94a3b8", strokeDasharray: "3 3" }} />
          <Line
            type="monotone"
            dataKey="average_score"
            stroke="#1e40af"
            strokeWidth={2}
            dot={{ r: 4, fill: "#1e40af", stroke: "#fff", strokeWidth: 2 }}
            activeDot={{ r: 5, fill: "#1e40af", stroke: "#fff", strokeWidth: 2 }}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </figure>
  );
}

type SeverityRow = { severity: keyof typeof SEVERITY_COLOR; label: string; count: number };

function SeverityTooltip({ active, payload }: TooltipContentProps) {
  const row = payload?.[0]?.payload as SeverityRow | undefined;
  if (!active || !row) return null;
  return <TooltipBox title={`${row.label} severity`} lines={[`${row.count} incident${row.count === 1 ? "" : "s"}`]} />;
}

export function SeverityChart({ data }: { data: DashboardSummary["incidents_by_severity"] }) {
  const rows: SeverityRow[] = data.map((row) => ({
    severity: row.severity,
    label: INCIDENT_SEVERITY[row.severity],
    count: row.count,
  }));
  const summary = rows.map((row) => `${row.label}: ${row.count}`).join("; ");

  return (
    <figure className="h-56" aria-label={`Incidents in the last 90 days by severity. ${summary}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 28, bottom: 0, left: 8 }} barCategoryGap={10}>
          <CartesianGrid stroke={GRID} horizontal={false} />
          <XAxis type="number" allowDecimals={false} tick={AXIS} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="label" tick={AXIS} tickLine={false} axisLine={false} width={64} />
          <Tooltip content={SeverityTooltip} cursor={{ fill: "#f1f5f9" }} />
          <Bar
            dataKey="count"
            radius={[0, 4, 4, 0]}
            maxBarSize={22}
            isAnimationActive={false}
            label={{ position: "right", fontSize: 12, fill: "#334155" }}
          >
            {rows.map((row) => (
              <Cell key={row.severity} fill={SEVERITY_COLOR[row.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}
