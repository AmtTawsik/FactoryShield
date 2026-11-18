"use client";

import { useState } from "react";
import { FormDialog } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/form";
import { useToast } from "@/components/ui/toast";
import { useAllFactories } from "@/hooks/use-factories";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useSubmit } from "@/hooks/use-submit";
import { api } from "@/lib/api";
import { isoToLocalInput, localInputToIso, nowLocalInput } from "@/lib/format";
import { OPTIONS } from "@/lib/labels";
import type { Incident, IncidentStatus } from "@/lib/types";

type FormState = {
  factory_id: string;
  occurred_at: string;
  incident_type: string;
  severity: string;
  location: string;
  injured_count: string;
  description: string;
  status: IncidentStatus;
};

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!form.factory_id) errors.factory_id = "Choose a factory";
  if (!form.occurred_at) errors.occurred_at = "Enter when it happened";
  else if (form.occurred_at > nowLocalInput()) errors.occurred_at = "The time cannot be in the future";
  if (!form.incident_type) errors.incident_type = "Choose the incident type";
  if (!form.severity) errors.severity = "Choose the severity";
  if (form.location.trim().length < 2) errors.location = "Enter where it happened";
  const injured = Number(form.injured_count);
  if (form.injured_count === "" || !Number.isInteger(injured) || injured < 0 || injured > 1000) {
    errors.injured_count = "Enter a number from 0 to 1,000";
  }
  if (form.description.trim().length < 10) errors.description = "Describe what happened (at least 10 characters)";
  return errors;
}

export function IncidentFormDialog({
  incident,
  factoryId,
  onClose,
}: {
  incident?: Incident;
  factoryId?: number;
  onClose: () => void;
}) {
  const factories = useAllFactories();
  const [form, setForm] = useState<FormState>(() => ({
    factory_id: String(incident?.factory_id ?? factoryId ?? ""),
    occurred_at: incident ? isoToLocalInput(incident.occurred_at) : nowLocalInput(),
    incident_type: incident?.incident_type ?? "",
    severity: incident?.severity ?? "",
    location: incident?.location ?? "",
    injured_count: String(incident?.injured_count ?? 0),
    description: incident?.description ?? "",
    status: incident?.status ?? "open",
  }));
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((current) => ({ ...current, [key]: value }));

  async function submit() {
    const common = {
      occurred_at: localInputToIso(form.occurred_at),
      incident_type: form.incident_type,
      severity: form.severity,
      location: form.location,
      injured_count: Number(form.injured_count),
      description: form.description,
      status: form.status,
    };
    const saved = await run(
      () =>
        incident
          ? api<Incident>(`/incidents/${incident.id}`, { method: "PATCH", body: common })
          : api<Incident>("/incidents", { method: "POST", body: { ...common, factory_id: Number(form.factory_id) } }),
      validate(form),
    );
    if (!saved) return;
    await revalidate("/incidents");
    toast.success(incident ? "Incident updated" : "Incident reported");
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title={incident ? "Edit incident" : "Report an incident"}
      description={incident ? factories.nameOf(incident.factory_id) : "Record an accident, fire, near miss or other safety event."}
      onSubmit={submit}
      submitLabel={incident ? "Save changes" : "Report incident"}
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
            disabled={Boolean(incident) || Boolean(factoryId)}
          />
        </Field>
        <Field label="Date and time" required error={fieldErrors.occurred_at} hint="Bangladesh time">
          <Input
            type="datetime-local"
            value={form.occurred_at}
            max={nowLocalInput()}
            onChange={(event) => set("occurred_at", event.target.value)}
          />
        </Field>
        <Field label="Location" required error={fieldErrors.location}>
          <Input
            value={form.location}
            onChange={(event) => set("location", event.target.value)}
            placeholder="Cutting section, floor 2"
            maxLength={120}
          />
        </Field>
        <Field label="Type" required error={fieldErrors.incident_type}>
          <Select
            value={form.incident_type}
            onChange={(event) => set("incident_type", event.target.value)}
            options={OPTIONS.incidentType}
            placeholder="Choose a type"
          />
        </Field>
        <Field label="Severity" required error={fieldErrors.severity}>
          <Select
            value={form.severity}
            onChange={(event) => set("severity", event.target.value)}
            options={OPTIONS.incidentSeverity}
            placeholder="Choose severity"
          />
        </Field>
        <Field label="People injured" required error={fieldErrors.injured_count}>
          <Input
            type="number"
            min={0}
            max={1000}
            inputMode="numeric"
            value={form.injured_count}
            onChange={(event) => set("injured_count", event.target.value)}
          />
        </Field>
        <Field label="Status" required error={fieldErrors.status}>
          <Select
            value={form.status}
            onChange={(event) => set("status", event.target.value as IncidentStatus)}
            options={OPTIONS.incidentStatus}
          />
        </Field>
        <Field label="Description" required error={fieldErrors.description} className="sm:col-span-2">
          <Textarea
            value={form.description}
            onChange={(event) => set("description", event.target.value)}
            maxLength={5000}
            placeholder="What happened, who was involved and what was done immediately"
          />
        </Field>
      </div>
    </FormDialog>
  );
}
