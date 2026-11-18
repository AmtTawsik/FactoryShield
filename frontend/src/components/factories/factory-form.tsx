"use client";

import { useState } from "react";
import { FormDialog } from "@/components/ui/dialog";
import { Checkbox, Field, Input } from "@/components/ui/form";
import { useToast } from "@/components/ui/toast";
import { useRevalidate } from "@/hooks/use-revalidate";
import { useSubmit } from "@/hooks/use-submit";
import { api } from "@/lib/api";
import type { Factory } from "@/lib/types";

type FormState = {
  name: string;
  license_number: string;
  address: string;
  district: string;
  worker_count: string;
  floor_count: string;
  contact_person: string;
  contact_phone: string;
  is_active: boolean;
};

function initialState(factory?: Factory): FormState {
  return {
    name: factory?.name ?? "",
    license_number: factory?.license_number ?? "",
    address: factory?.address ?? "",
    district: factory?.district ?? "",
    worker_count: factory ? String(factory.worker_count) : "",
    floor_count: factory ? String(factory.floor_count) : "",
    contact_person: factory?.contact_person ?? "",
    contact_phone: factory?.contact_phone ?? "",
    is_active: factory?.is_active ?? true,
  };
}

function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (form.name.trim().length < 2) errors.name = "Enter the factory name";
  if (!form.license_number.trim()) errors.license_number = "Enter the licence number";
  if (form.address.trim().length < 5) errors.address = "Enter the full address";
  if (form.district.trim().length < 2) errors.district = "Enter the district";
  if (!(Number(form.worker_count) > 0)) errors.worker_count = "Enter the number of workers";
  if (!(Number(form.floor_count) > 0)) errors.floor_count = "Enter the number of floors";
  if (form.contact_person.trim().length < 2) errors.contact_person = "Enter the contact person";
  if (!form.contact_phone.trim()) errors.contact_phone = "Enter a mobile number";
  return errors;
}

export function FactoryFormDialog({
  factory,
  onClose,
  onSaved,
}: {
  factory?: Factory;
  onClose: () => void;
  onSaved?: (factory: Factory) => void;
}) {
  const [form, setForm] = useState(() => initialState(factory));
  const { run, saving, error, fieldErrors } = useSubmit();
  const revalidate = useRevalidate();
  const toast = useToast();

  const text = (key: keyof FormState) => ({
    value: form[key] as string,
    onChange: (event: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [key]: event.target.value }),
  });

  async function submit() {
    const payload = {
      name: form.name,
      license_number: form.license_number,
      address: form.address,
      district: form.district,
      worker_count: Number(form.worker_count),
      floor_count: Number(form.floor_count),
      contact_person: form.contact_person,
      contact_phone: form.contact_phone,
      ...(factory ? { is_active: form.is_active } : {}),
    };
    const saved = await run(
      () =>
        factory
          ? api<Factory>(`/factories/${factory.id}`, { method: "PATCH", body: payload })
          : api<Factory>("/factories", { method: "POST", body: payload }),
      validate(form),
    );
    if (!saved) return;
    await revalidate("/factories");
    toast.success(factory ? "Factory updated" : `${saved.name} added`);
    onSaved?.(saved);
    onClose();
  }

  return (
    <FormDialog
      open
      onClose={onClose}
      title={factory ? "Edit factory" : "Add factory"}
      description={factory ? factory.name : "Register a factory to start tracking its safety records."}
      onSubmit={submit}
      submitLabel={factory ? "Save changes" : "Add factory"}
      saving={saving}
      error={error}
      size="lg"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Factory name" required error={fieldErrors.name} className="sm:col-span-2">
          <Input {...text("name")} placeholder="e.g. Sonali Thread Knit Composite Ltd" maxLength={150} />
        </Field>
        <Field label="Licence number" required error={fieldErrors.license_number} hint="Letters, numbers, '-' and '/'">
          <Input {...text("license_number")} placeholder="FL-GZP-04512" maxLength={50} />
        </Field>
        <Field label="District" required error={fieldErrors.district}>
          <Input {...text("district")} placeholder="Gazipur" maxLength={50} />
        </Field>
        <Field label="Address" required error={fieldErrors.address} className="sm:col-span-2">
          <Input {...text("address")} placeholder="Plot 14, Konabari BSCIC Industrial Area" maxLength={255} />
        </Field>
        <Field label="Workers" required error={fieldErrors.worker_count}>
          <Input {...text("worker_count")} type="number" min={1} max={100000} inputMode="numeric" />
        </Field>
        <Field label="Floors" required error={fieldErrors.floor_count}>
          <Input {...text("floor_count")} type="number" min={1} max={50} inputMode="numeric" />
        </Field>
        <Field label="Contact person" required error={fieldErrors.contact_person}>
          <Input {...text("contact_person")} placeholder="Kamrul Islam" maxLength={120} />
        </Field>
        <Field label="Contact mobile" required error={fieldErrors.contact_phone} hint="Bangladeshi mobile, e.g. 01711-234567">
          <Input {...text("contact_phone")} type="tel" placeholder="01711-234567" maxLength={20} />
        </Field>
        {factory && (
          <Checkbox
            className="sm:col-span-2"
            label="Active"
            description="Inactive factories keep their records but are not counted as active factories."
            checked={form.is_active}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
        )}
      </div>
    </FormDialog>
  );
}
