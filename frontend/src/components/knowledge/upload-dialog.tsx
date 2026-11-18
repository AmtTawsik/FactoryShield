"use client";

import { FileText, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { FormDialog } from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/form";
import { InlineAlert } from "@/components/ui/states";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useSubmit } from "@/hooks/use-submit";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { todayInDhaka } from "@/lib/format";
import { OPTIONS } from "@/lib/labels";
import type { ContentStatus, IngestResult } from "@/lib/types";

const MAX_BYTES = 10 * 1024 * 1024;
const ACCEPTED = [".pdf", ".txt", ".md"];

type FormState = {
  title: string;
  source_authority: string;
  category: string;
  content_status: ContentStatus;
  source_url: string;
  verified_on: string;
  factory_id: string;
};

function titleFromFileName(name: string) {
  const base = name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ").trim();
  return base.charAt(0).toUpperCase() + base.slice(1);
}

function formatSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function UploadDialog({ onClose }: { onClose: () => void }) {
  const factories = useAllFactories();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [form, setForm] = useState<FormState>({
    title: "",
    source_authority: "",
    category: "",
    content_status: "general_guidance",
    source_url: "",
    verified_on: "",
    factory_id: "",
  });
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((current) => ({ ...current, [key]: value }));

  function choose(selected: File | undefined) {
    if (!selected) return;
    setFile(selected);
    if (!form.title) set("title", titleFromFileName(selected.name));
  }

  function validate(): Record<string, string> {
    const errors: Record<string, string> = {};
    if (!file) errors.file = "Choose a PDF, TXT or MD file";
    else if (!ACCEPTED.some((ext) => file.name.toLowerCase().endsWith(ext))) errors.file = "Only PDF, TXT and MD files are supported";
    else if (file.size > MAX_BYTES) errors.file = "The file is larger than 10 MB";
    if (form.title.trim().length < 3) errors.title = "Enter a title (at least 3 characters)";
    if (form.source_authority.trim().length < 2) errors.source_authority = "Enter who published this document";
    if (!form.category) errors.category = "Choose a category";
    if (form.source_url && !/^https?:\/\/\S+$/.test(form.source_url.trim())) errors.source_url = "Enter a full link starting with https://";
    if (form.content_status === "official_verified") {
      if (!form.source_url.trim()) errors.source_url = "An official document needs the source link";
      if (!form.verified_on) errors.verified_on = "Enter the date you checked the source";
    }
    return errors;
  }

  async function submit() {
    const result = await run(() => {
      const body = new FormData();
      body.set("file", file as File);
      for (const [key, value] of Object.entries(form)) {
        if (value.trim()) body.set(key, value.trim());
      }
      return api<IngestResult>("/knowledge/documents", { method: "POST", body });
    }, validate());
    if (!result) return;
    await revalidate("/knowledge");
    const message = {
      created: `Document added (${result.chunk_count} passages indexed)`,
      updated: `Document replaced with the new file (${result.chunk_count} passages indexed)`,
      unchanged: "This file is already in the knowledge base. Nothing changed.",
    }[result.status];
    toast.success(message);
    onClose();
  }

  const official = form.content_status === "official_verified";

  return (
    <FormDialog
      open
      onClose={onClose}
      title="Upload document"
      description="The text is split into passages and indexed so the AI Assistant can cite it."
      onSubmit={submit}
      submitLabel={saving ? "Uploading and indexing…" : "Upload"}
      saving={saving}
      error={error}
    >
      <Field label="File" required error={fieldErrors.file}>
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            choose(event.dataTransfer.files[0]);
          }}
          className={cn(
            "flex flex-col items-center rounded-md border border-dashed px-4 py-6 text-center",
            dragging ? "border-brand-500 bg-brand-50" : fieldErrors.file ? "border-red-400" : "border-slate-300",
          )}
        >
          {file ? (
            <div className="flex items-center gap-2 text-sm">
              <FileText className="size-5 text-brand-600" aria-hidden="true" />
              <span className="font-medium text-slate-900">{file.name}</span>
              <span className="text-slate-500">({formatSize(file.size)})</span>
            </div>
          ) : (
            <>
              <UploadCloud className="size-6 text-slate-400" aria-hidden="true" />
              <p className="mt-2 text-sm text-slate-600">Drag a file here, or choose one</p>
              <p className="text-xs text-slate-500">PDF with selectable text, TXT or MD (UTF-8). Up to 10 MB.</p>
            </>
          )}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {file ? "Choose another file" : "Choose file"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(",")}
            className="sr-only"
            tabIndex={-1}
            aria-hidden="true"
            onChange={(event) => choose(event.target.files?.[0])}
          />
        </div>
      </Field>

      <Field label="Title" required error={fieldErrors.title}>
        <Input value={form.title} onChange={(event) => set("title", event.target.value)} maxLength={200} />
      </Field>
      <Field label="Published by" required error={fieldErrors.source_authority} hint="The organisation or team that issued it">
        <Input
          value={form.source_authority}
          onChange={(event) => set("source_authority", event.target.value)}
          placeholder="e.g. Department of Inspection for Factories and Establishments (DIFE)"
          maxLength={200}
        />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Category" required error={fieldErrors.category}>
          <Select
            value={form.category}
            onChange={(event) => set("category", event.target.value)}
            options={OPTIONS.knowledgeCategory}
            placeholder="Choose a category"
          />
        </Field>
        <Field label="Applies to" error={fieldErrors.factory_id}>
          <Select
            value={form.factory_id}
            onChange={(event) => set("factory_id", event.target.value)}
            options={factories.options}
            placeholder="All factories (general)"
          />
        </Field>
        <Field label="Content type" required error={fieldErrors.content_status}>
          <Select
            value={form.content_status}
            onChange={(event) => set("content_status", event.target.value as ContentStatus)}
            options={OPTIONS.contentStatus}
          />
        </Field>
        <Field label="Verified on" required={official} error={fieldErrors.verified_on}>
          <Input
            type="date"
            value={form.verified_on}
            max={todayInDhaka()}
            onChange={(event) => set("verified_on", event.target.value)}
          />
        </Field>
        <Field label="Source link" required={official} error={fieldErrors.source_url} className="sm:col-span-2">
          <Input
            type="url"
            value={form.source_url}
            onChange={(event) => set("source_url", event.target.value)}
            placeholder="https://"
          />
        </Field>
      </div>
      {official && (
        <InlineAlert tone="info">
          Mark a document as official only when you have checked it against the published source.
        </InlineAlert>
      )}
      {saving && (
        <InlineAlert tone="info">Reading the file and indexing it. Large PDFs can take a minute; please keep this window open.</InlineAlert>
      )}
    </FormDialog>
  );
}
