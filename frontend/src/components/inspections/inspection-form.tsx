"use client";

import { useState } from "react";
import useSWR from "swr";
import { FormDialog } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useSubmit } from "@/hooks/use-submit";
import { api } from "@/lib/api";
import { todayInDhaka } from "@/lib/format";
import { OPTIONS } from "@/lib/labels";
import type { Inspection, InspectionCategory, InspectionStatus, Page, UserDetail } from "@/lib/types";

type FormState = {
  factory_id: string;
  inspection_date: string;
  category: string;
  status: InspectionStatus;
  score: string;
  inspector_id: string;
  findings: string;
};

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!form.factory_id) errors.factory_id = "Choose a factory";
  if (!form.inspection_date) errors.inspection_date = "Choose the inspection date";
  if (!form.category) errors.category = "Choose a category";
  if (form.status === "completed") {
    const score = Number(form.score);
    if (form.score === "" || !Number.isInteger(score) || score < 0 || score > 100) {
      errors.score = "A completed inspection needs a whole-number score from 0 to 100";
    }
    if (form.inspection_date > todayInDhaka()) errors.inspection_date = "A completed inspection cannot have a future date";
  }
  return errors;
}

export function InspectionFormDialog({
  inspection,
  factoryId,
  onClose,
}: {
  inspection?: Inspection;
  factoryId?: number;
  onClose: () => void;
}) {
  const factories = useAllFactories();
  const { data: users } = useSWR<Page<UserDetail>>("/users?is_active=true&size=100");
  const [form, setForm] = useState<FormState>(() => ({
    factory_id: String(inspection?.factory_id ?? factoryId ?? ""),
    inspection_date: inspection?.inspection_date ?? todayInDhaka(),
    category: inspection?.category ?? "",
    status: inspection?.status ?? "scheduled",
    score: inspection?.score?.toString() ?? "",
    inspector_id: inspection?.inspector_id?.toString() ?? "",
    findings: inspection?.findings ?? "",
  }));
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((current) => ({ ...current, [key]: value }));

  const inspectorOptions = (users?.items ?? []).map((user) => ({ value: String(user.id), label: user.full_name }));
  if (inspection?.inspector_id && !inspectorOptions.some((option) => option.value === String(inspection.inspector_id))) {
    inspectorOptions.push({ value: String(inspection.inspector_id), label: `User #${inspection.inspector_id}` });
  }

  async function submit() {
    const completed = form.status === "completed";
    const common = {
      inspection_date: form.inspection_date,
      category: form.category as InspectionCategory,
      status: form.status,
      score: completed ? Number(form.score) : null,
      inspector_id: form.inspector_id ? Number(form.inspector_id) : null,
      findings: form.findings.trim() || null,
    };
    const saved = await run(
      () =>
        inspection
          ? api<Inspection>(`/inspections/${inspection.id}`, { method: "PATCH", body: common })
          : api<Inspection>("/inspections", { method: "POST", body: { ...common, factory_id: Number(form.factory_id) } }),
      validate(form),
    );
    if (!saved) return;
    await revalidate("/inspections");
    toast.success(inspection ? "Inspection updated" : "Inspection saved");
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title={inspection ? "Edit inspection" : "New safety inspection"}
      description={inspection ? factories.nameOf(inspection.factory_id) : "Schedule an inspection or record a completed one."}
      onSubmit={submit}
      submitLabel={inspection ? "Save changes" : "Save inspection"}
      saving={saving}
      error={error}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Factory" required error={fieldErrors.factory_id} className="sm:col-span-2">
          <Select
            value={form.factory_id}
            onChange={(event) => set("factory_id", event.target.value)}
            options={factories.options}
            placeholder={factories.isLoading ? "Loading factories…" : "Choose a factory"}
            disabled={Boolean(inspection) || Boolean(factoryId)}
          />
        </Field>
        <Field label="Category" required error={fieldErrors.category}>
          <Select
            value={form.category}
            onChange={(event) => set("category", event.target.value)}
            options={OPTIONS.inspectionCategory}
            placeholder="Choose a category"
          />
        </Field>
        <Field label="Inspection date" required error={fieldErrors.inspection_date}>
          <Input type="date" value={form.inspection_date} onChange={(event) => set("inspection_date", event.target.value)} />
        </Field>
        <Field label="Status" required error={fieldErrors.status}>
          <Select
            value={form.status}
            onChange={(event) => set("status", event.target.value as InspectionStatus)}
            options={OPTIONS.inspectionStatus}
          />
        </Field>
        <Field
          label="Score"
          required={form.status === "completed"}
          error={fieldErrors.score}
          hint={form.status === "completed" ? "0 to 100" : "Added when the inspection is completed"}
        >
          <Input
            type="number"
            min={0}
            max={100}
            inputMode="numeric"
            value={form.status === "completed" ? form.score : ""}
            onChange={(event) => set("score", event.target.value)}
            disabled={form.status !== "completed"}
          />
        </Field>
        <Field label="Inspector" error={fieldErrors.inspector_id} className="sm:col-span-2">
          <Select
            value={form.inspector_id}
            onChange={(event) => set("inspector_id", event.target.value)}
            options={inspectorOptions}
            placeholder="Not assigned"
          />
        </Field>
        <Field label="Findings" error={fieldErrors.findings} className="sm:col-span-2" hint="Up to 5,000 characters">
          <Textarea
            value={form.findings}
            onChange={(event) => set("findings", event.target.value)}
            maxLength={5000}
            placeholder="What was checked and what needs attention"
          />
        </Field>
      </div>
    </FormDialog>
  );
}
