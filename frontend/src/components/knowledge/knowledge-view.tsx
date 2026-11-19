"use client";

import { BookOpen, ExternalLink, Upload } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";
import { useSession } from "@/components/shell/session";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, PageHeader } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/dialog";
import { FilterSelect } from "@/components/ui/form";
import { RowActions } from "@/components/ui/row-actions";
import { FilterBar, SearchInput } from "@/components/ui/search-input";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/ui/states";
import { Pagination, Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { api, errorMessage, withQuery } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { KNOWLEDGE_CATEGORY, OPTIONS } from "@/lib/labels";
import type { KnowledgeDocument, Page } from "@/lib/types";
import { UploadDialog } from "./upload-dialog";

const FILTERS = ["search", "category", "content_status", "factory_id", "shared"] as const;

export function ContentStatusBadge({ status, verifiedOn }: { status: KnowledgeDocument["content_status"]; verifiedOn: string | null }) {
  return status === "official_verified" ? (
    <Badge tone="success">Official · verified {verifiedOn ? formatDate(verifiedOn) : ""}</Badge>
  ) : (
    <Badge>General guidance</Badge>
  );
}

export function KnowledgeView() {
  const { isAdmin, isSuperAdmin } = useSession();
  const factories = useAllFactories(!isSuperAdmin);
  const canDelete = (document: KnowledgeDocument) =>
    isSuperAdmin ? document.organization_id === null : isAdmin && document.organization_id !== null;
  const { values, update, clear, activeCount } = useUrlFilters(FILTERS);
  const { data, error, isLoading, mutate } = useSWR<Page<KnowledgeDocument>>(withQuery("/knowledge/documents", values));
  const revalidate = useRevalidate();
  const toast = useToast();
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<KnowledgeDocument | null>(null);

  return (
    <>
      <PageHeader
        title={isSuperAdmin ? "Shared library" : "Knowledge documents"}
        description={
          isSuperAdmin
            ? "Laws and safety guidance every organization sees and the AI Assistant cites."
            : "The shared library plus your organization's own procedures. The AI Assistant searches and cites them."
        }
        actions={
          (isAdmin || isSuperAdmin) && (
            <Button icon={<Upload className="size-4" aria-hidden="true" />} onClick={() => setUploading(true)}>
              Upload document
            </Button>
          )
        }
      />

      <Card>
        <FilterBar activeCount={activeCount} onClear={clear}>
          <SearchInput
            value={values.search}
            onChange={(search) => update({ search })}
            placeholder="Search title or publisher"
            className="w-full sm:w-64"
          />
          <FilterSelect
            label="Category"
            value={values.category}
            onChange={(category) => update({ category })}
            options={OPTIONS.knowledgeCategory}
            allLabel="All categories"
            className="w-full sm:w-48"
          />
          <FilterSelect
            label="Content type"
            value={values.content_status}
            onChange={(content_status) => update({ content_status })}
            options={OPTIONS.contentStatus}
            allLabel="Any content type"
            className="w-full sm:w-44"
          />
          {!isSuperAdmin && (
            <>
              <FilterSelect
                label="Source"
                value={values.shared}
                onChange={(shared) => update({ shared })}
                options={[
                  { value: "true", label: "Shared library" },
                  { value: "false", label: "Our documents" },
                ]}
                allLabel="All sources"
                className="w-full sm:w-40"
              />
              <FilterSelect
                label="Factory"
                value={values.factory_id}
                onChange={(factory_id) => update({ factory_id })}
                options={factories.options}
                allLabel="Any factory"
                className="w-full sm:w-52"
              />
            </>
          )}
        </FilterBar>

        {error ? (
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
        ) : isLoading || !data ? (
          <TableSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="size-5" aria-hidden="true" />}
            title={activeCount ? "No documents match these filters" : "No documents yet"}
            description={
              activeCount
                ? "Try a different search or clear the filters."
                : "Uploaded documents are indexed so the assistant can answer from them."
            }
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Document</Th>
                <Th className="hidden md:table-cell">Category</Th>
                <Th>Type</Th>
                {!isSuperAdmin && <Th className="hidden lg:table-cell">Applies to</Th>}
                <Th className="hidden text-right sm:table-cell">Passages</Th>
                <Th className="hidden xl:table-cell">Updated</Th>
                {(isAdmin || isSuperAdmin) && <Th className="w-14"><span className="sr-only">Actions</span></Th>}
              </THead>
              <TBody>
                {data.items.map((document) => (
                  <Tr key={document.id}>
                    <Td className="max-w-md">
                      <p className="font-medium text-slate-900">{document.title}</p>
                      <p className="flex items-center gap-1 truncate text-xs text-slate-500">
                        {document.source_authority}
                        {document.source_url && (
                          <a
                            href={document.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-0.5 text-brand-700 hover:underline"
                          >
                            · Source <ExternalLink className="size-3" aria-hidden="true" />
                            <span className="sr-only">(opens in a new tab)</span>
                          </a>
                        )}
                      </p>
                    </Td>
                    <Td className="hidden md:table-cell">{KNOWLEDGE_CATEGORY[document.category]}</Td>
                    <Td>
                      <ContentStatusBadge status={document.content_status} verifiedOn={document.verified_on} />
                    </Td>
                    {!isSuperAdmin && (
                      <Td className="hidden max-w-48 truncate lg:table-cell">
                        {document.organization_id === null ? (
                          <Badge tone="brand">Shared library</Badge>
                        ) : document.factory_id ? (
                          factories.nameOf(document.factory_id)
                        ) : (
                          <span className="text-slate-600">Whole organization</span>
                        )}
                      </Td>
                    )}
                    <Td className="hidden text-right tabular-nums sm:table-cell">{document.chunk_count}</Td>
                    <Td className="hidden whitespace-nowrap xl:table-cell">{formatDate(document.updated_at)}</Td>
                    {(isAdmin || isSuperAdmin) && (
                      <Td>
                        {canDelete(document) && <RowActions label={document.title} onDelete={() => setDeleting(document)} />}
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

      {uploading && <UploadDialog onClose={() => setUploading(false)} />}
      <ConfirmDialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title="Delete document?"
        description={
          deleting && (
            <>
              <strong>{deleting.title}</strong> and its {deleting.chunk_count} indexed passages will be removed. The
              assistant will no longer use it{isSuperAdmin ? " for any organization" : ""}. Earlier answers are not changed.
            </>
          )
        }
        onConfirm={async () => {
          if (!deleting) return;
          await api(`/knowledge/documents/${deleting.id}`, { method: "DELETE" });
          await revalidate("/knowledge");
          toast.success("Document deleted");
        }}
      />
    </>
  );
}
