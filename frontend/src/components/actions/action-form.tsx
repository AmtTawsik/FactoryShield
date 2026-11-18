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
import { formatDate, formatDateTime } from "@/lib/format";
import { INCIDENT_TYPE, INSPECTION_CATEGORY, OPTIONS } from "@/lib/labels";
import type { ActionPriority, ActionStatus, CorrectiveAction, Incident, Inspection, Page } from "@/lib/types";

type FormState = {
  factory_id: string;
  title: string;
  description: string;
  priority: ActionPriority;
  assigned_to: string;
  due_date: string;
  status: ActionStatus;
  inspection_id: string;
  incident_id: string;
};

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!form.factory_id) errors.factory_id = "Choose a factory";
  if (form.title.trim().length < 5) errors.title = "Describe the action in at least 5 characters";
  if (form.assigned_to.trim().length < 2) errors.assigned_to = "Enter who is responsible";
  if (!form.due_date) errors.due_date = "Choose a due date";
  return errors;
}

export function ActionFormDialog({
  action,
  factoryId,
  inspectionId,
  incidentId,
  onClose,
}: {
  action?: CorrectiveAction;
  factoryId?: number;
  inspectionId?: number;
  incidentId?: number;
  onClose: () => void;
}) {
  const factories = useAllFactories();
  const [form, setForm] = useState<FormState>(() => ({
    factory_id: String(action?.factory_id ?? factoryId ?? ""),
    title: action?.title ?? "",
    description: action?.description ?? "",
    priority: action?.priority ?? "medium",
    assigned_to: action?.assigned_to ?? "",
    due_date: action?.due_date ?? "",
    status: action?.status ?? "open",
    inspection_id: String(action?.inspection_id ?? inspectionId ?? ""),
    incident_id: String(action?.incident_id ?? incidentId ?? ""),
  }));
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  const linkQuery = form.factory_id ? `factory_id=${form.factory_id}&size=100` : null;
  const { data: inspections } = useSWR<Page<Inspection>>(linkQuery && `/inspections?${linkQuery}`);
  const { data: incidents } = useSWR<Page<Incident>>(linkQuery && `/incidents?${linkQuery}`);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((current) => ({ ...current, [key]: value }));

  async function submit() {
    const common = {
      title: form.title,
      description: form.description.trim() || null,
      priority: form.priority,
      assigned_to: form.assigned_to,
      due_date: form.due_date,
      status: form.status,
      inspection_id: form.inspection_id ? Number(form.inspection_id) : null,
      incident_id: form.incident_id ? Number(form.incident_id) : null,
    };
    const saved = await run(
      () =>
        action
          ? api<CorrectiveAction>(`/corrective-actions/${action.id}`, { method: "PATCH", body: common })
          : api<CorrectiveAction>("/corrective-actions", {
              method: "POST",
              body: { ...common, factory_id: Number(form.factory_id) },
            }),
      validate(form),
    );
    if (!saved) return;
    await revalidate("/corrective-actions");
    toast.success(action ? "Corrective action updated" : "Corrective action created");
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title={action ? "Edit corrective action" : "New corrective action"}
      description={action ? factories.nameOf(action.factory_id) : "Assign a fix with an owner and a due date."}
      onSubmit={submit}
      submitLabel={action ? "Save changes" : "Create action"}
      saving={saving}
      error={error}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Factory" required error={fieldErrors.factory_id} className="sm:col-span-2">
          <Select
            value={form.factory_id}
            onChange={(event) => setForm({ ...form, factory_id: event.target.value, inspection_id: "", incident_id: "" })}
            options={factories.options}
            placeholder={factories.isLoading ? "Loading factories…" : "Choose a factory"}
            disabled={Boolean(action) || Boolean(factoryId)}
          />
        </Field>
        <Field label="Action" required error={fieldErrors.title} className="sm:col-span-2">
          <Input
            value={form.title}
            onChange={(event) => set("title", event.target.value)}
            placeholder="e.g. Refill expired extinguishers on floor 3"
            maxLength={200}
          />
        </Field>
        <Field label="Responsible person or team" required error={fieldErrors.assigned_to}>
          <Input
            value={form.assigned_to}
            onChange={(event) => set("assigned_to", event.target.value)}
            placeholder="Fire Safety Officer"
            maxLength={120}
          />
        </Field>
        <Field label="Due date" required error={fieldErrors.due_date}>
          <Input type="date" value={form.due_date} onChange={(event) => set("due_date", event.target.value)} />
        </Field>
        <Field label="Priority" required error={fieldErrors.priority}>
          <Select
            value={form.priority}
            onChange={(event) => set("priority", event.target.value as ActionPriority)}
            options={OPTIONS.actionPriority}
          />
        </Field>
        <Field label="Status" required error={fieldErrors.status}>
          <Select
            value={form.status}
            onChange={(event) => set("status", event.target.value as ActionStatus)}
            options={OPTIONS.actionStatus}
          />
        </Field>
        <Field label="Linked inspection" error={fieldErrors.inspection_id}>
          <Select
            value={form.inspection_id}
            onChange={(event) => set("inspection_id", event.target.value)}
            options={(inspections?.items ?? []).map((item) => ({
              value: String(item.id),
              label: `${formatDate(item.inspection_date)} · ${INSPECTION_CATEGORY[item.category]}`,
            }))}
            placeholder={form.factory_id ? "None" : "Choose a factory first"}
            disabled={!form.factory_id}
          />
        </Field>
        <Field label="Linked incident" error={fieldErrors.incident_id}>
          <Select
            value={form.incident_id}
            onChange={(event) => set("incident_id", event.target.value)}
            options={(incidents?.items ?? []).map((item) => ({
              value: String(item.id),
              label: `${formatDateTime(item.occurred_at)} · ${INCIDENT_TYPE[item.incident_type]}`,
            }))}
            placeholder={form.factory_id ? "None" : "Choose a factory first"}
            disabled={!form.factory_id}
          />
        </Field>
        <Field label="Details" error={fieldErrors.description} className="sm:col-span-2">
          <Textarea
            value={form.description}
            onChange={(event) => set("description", event.target.value)}
            maxLength={5000}
            rows={3}
            placeholder="Steps, materials or notes for the responsible person"
          />
        </Field>
      </div>
    </FormDialog>
  );
}
