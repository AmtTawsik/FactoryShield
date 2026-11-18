"use client";

import { Building2, Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, PageHeader } from "@/components/ui/card";
import { FilterSelect } from "@/components/ui/form";
import { ExportButton, type CsvColumn } from "@/components/ui/export-button";
import { FilterBar, SearchInput } from "@/components/ui/search-input";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { errorMessage, withQuery } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { Factory, Page } from "@/lib/types";
import { FactoryFormDialog } from "./factory-form";

const FILTERS = ["search", "district", "is_active"] as const;

const CSV_COLUMNS: CsvColumn<Factory>[] = [
  { header: "Factory", value: (f) => f.name },
  { header: "Licence number", value: (f) => f.license_number },
  { header: "District", value: (f) => f.district },
  { header: "Address", value: (f) => f.address },
  { header: "Workers", value: (f) => f.worker_count },
  { header: "Floors", value: (f) => f.floor_count },
  { header: "Contact person", value: (f) => f.contact_person },
  { header: "Contact mobile", value: (f) => f.contact_phone },
  { header: "Status", value: (f) => (f.is_active ? "Active" : "Inactive") },
  { header: "Registered", value: (f) => f.created_at.slice(0, 10) },
];
const PAGE_SIZE = 20;

export function FactoriesView() {
  const { isAdmin } = useSession();
  const router = useRouter();
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const [creating, setCreating] = useState(false);
  const { data, error, isLoading, mutate } = useSWR<Page<Factory>>(
    withQuery("/factories", { ...values, size: PAGE_SIZE }),
  );

  return (
    <>
      <PageHeader
        title="Factories"
        description="Factories you manage, with their licence and contact details."
        actions={
          <>
            <ExportButton path="/factories" filters={values} columns={CSV_COLUMNS} fileName="factories" disabled={!data?.total} />
            {isAdmin && (
              <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
                Add factory
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
            placeholder="Search name or licence"
            className="w-full sm:w-72"
          />
          <SearchInput
            label="District"
            value={values.district}
            onChange={(district) => update({ district })}
            placeholder="District"
            className="w-full sm:w-44"
          />
          <FilterSelect
            label="Status"
            value={values.is_active}
            onChange={(is_active) => update({ is_active })}
            options={[
              { value: "true", label: "Active" },
              { value: "false", label: "Inactive" },
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
            icon={<Building2 className="size-5" aria-hidden="true" />}
            title={activeCount ? "No factories match these filters" : "No factories yet"}
            description={
              activeCount
                ? "Try a different search or clear the filters."
                : isAdmin
                  ? "Add the first factory to start tracking inspections and incidents."
                  : "No factory has been assigned to you yet. Ask an administrator."
            }
            action={
              isAdmin && !activeCount && (
                <Button icon={<Plus className="size-4" aria-hidden="true" />} onClick={() => setCreating(true)}>
                  Add factory
                </Button>
              )
            }
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Factory</Th>
                <Th>District</Th>
                <Th className="hidden md:table-cell">Licence</Th>
                <Th className="text-right">Workers</Th>
                <Th className="hidden text-right lg:table-cell">Floors</Th>
                <Th className="hidden lg:table-cell">Contact</Th>
                <Th>Status</Th>
              </THead>
              <TBody>
                {data.items.map((factory) => (
                  <Tr
                    key={factory.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/factories/${factory.id}`)}
                  >
                    <Td className="max-w-xs">
                      <Link
                        href={`/factories/${factory.id}`}
                        onClick={(event) => event.stopPropagation()}
                        className="font-medium text-slate-900 hover:text-brand-700"
                      >
                        {factory.name}
                      </Link>
                      <p className="truncate text-xs text-slate-500">{factory.address}</p>
                    </Td>
                    <Td>{factory.district}</Td>
                    <Td className="hidden font-mono text-xs md:table-cell">{factory.license_number}</Td>
                    <Td className="text-right tabular-nums">{formatNumber(factory.worker_count)}</Td>
                    <Td className="hidden text-right tabular-nums lg:table-cell">{factory.floor_count}</Td>
                    <Td className="hidden lg:table-cell">
                      <p>{factory.contact_person}</p>
                      <p className="text-xs text-slate-500">{factory.contact_phone}</p>
                    </Td>
                    <Td>
                      <Badge tone={factory.is_active ? "success" : "neutral"}>
                        {factory.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} size={data.size} total={data.total} onPageChange={(page) => update({ page })} />
          </>
        )}
      </Card>

      {creating && (
        <FactoryFormDialog
          onClose={() => setCreating(false)}
          onSaved={(factory) => router.push(`/factories/${factory.id}`)}
        />
      )}
    </>
  );
}
