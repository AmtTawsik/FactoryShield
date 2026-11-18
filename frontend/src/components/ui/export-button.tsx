"use client";

import { Download } from "lucide-react";
import { useState } from "react";
import { api, errorMessage } from "@/lib/api";
import { todayInDhaka } from "@/lib/format";
import type { Page } from "@/lib/types";
import { Button } from "./button";
import { useToast } from "./toast";

export type CsvColumn<T> = { header: string; value: (item: T) => string | number | boolean | null | undefined };

const PAGE_SIZE = 100;

function cell(value: string | number | boolean | null | undefined): string {
  let text = value === null || value === undefined ? "" : String(value);
  // Spreadsheet apps run text cells that start with these characters as formulas.
  if (typeof value === "string" && /^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function toCsv<T>(items: T[], columns: CsvColumn<T>[]): string {
  const lines = [columns.map((column) => cell(column.header)).join(",")];
  for (const item of items) lines.push(columns.map((column) => cell(column.value(item))).join(","));
  // The byte order mark makes Excel read the file as UTF-8 (needed for Bangla text).
  return `\ufeff${lines.join("\r\n")}\r\n`;
}

async function fetchAll<T>(path: string, query: Record<string, string>): Promise<T[]> {
  const items: T[] = [];
  for (let page = 1; ; page++) {
    const result = await api<Page<T>>(path, { query: { ...query, page, size: PAGE_SIZE } });
    items.push(...result.items);
    if (items.length >= result.total || result.items.length === 0) return items;
  }
}

/** Downloads every row that matches the current filters (all pages), not only the visible page. */
export function ExportButton<T>({
  path,
  filters,
  columns,
  fileName,
  disabled,
}: {
  path: string;
  filters: Record<string, string | number>;
  columns: CsvColumn<T>[];
  fileName: string;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function exportCsv() {
    setBusy(true);
    try {
      const query: Record<string, string> = {};
      for (const [key, value] of Object.entries(filters)) {
        if (key !== "page" && value !== "") query[key] = String(value);
      }
      const items = await fetchAll<T>(path, query);
      const url = URL.createObjectURL(new Blob([toCsv(items, columns)], { type: "text/csv;charset=utf-8" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${fileName}-${todayInDhaka()}.csv`;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast.success(`Exported ${items.length} row${items.length === 1 ? "" : "s"}`);
    } catch (caught) {
      toast.error(`Export failed. ${errorMessage(caught)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button
      variant="secondary"
      icon={<Download className="size-4" aria-hidden="true" />}
      onClick={exportCsv}
      loading={busy}
      disabled={disabled}
      title="Download all rows that match the current filters"
    >
      Export CSV
    </Button>
  );
}
