"use client";

import { createContext, use, useId, type ComponentProps, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import type { Option } from "@/lib/labels";

type FieldContext = { id: string; describedBy?: string; invalid: boolean };
const FieldCtx = createContext<FieldContext | null>(null);

function useFieldProps(id?: string) {
  const field = use(FieldCtx);
  return {
    id: id ?? field?.id,
    "aria-describedby": field?.describedBy,
    "aria-invalid": field?.invalid || undefined,
    invalid: field?.invalid ?? false,
  };
}

export function Field({
  label,
  hint,
  error,
  required,
  children,
  className,
}: {
  label: string;
  hint?: ReactNode;
  error?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [errorId, hintId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={cn("min-w-0", className)}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
        {required && (
          <span className="ml-0.5 text-red-600" aria-hidden="true">
            *
          </span>
        )}
      </label>
      <FieldCtx value={{ id, describedBy, invalid: Boolean(error) }}>{children}</FieldCtx>
      {error ? (
        <p id={errorId} className="mt-1.5 text-sm text-red-700">
          {error}
        </p>
      ) : (
        hint && (
          <p id={hintId} className="mt-1.5 text-xs text-slate-500">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

const CONTROL =
  "block w-full rounded-md border bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500";

function controlClass(invalid: boolean, className?: string) {
  return cn(CONTROL, invalid ? "border-red-400" : "border-slate-300", className);
}

export function Input({ className, id, ...props }: ComponentProps<"input">) {
  const { invalid, ...field } = useFieldProps(id);
  return <input className={controlClass(invalid, cn("h-9", className))} {...field} {...props} />;
}

export function Textarea({ className, id, rows = 4, ...props }: ComponentProps<"textarea">) {
  const { invalid, ...field } = useFieldProps(id);
  return <textarea rows={rows} className={controlClass(invalid, cn("py-2", className))} {...field} {...props} />;
}

type SelectProps = Omit<ComponentProps<"select">, "children"> & {
  options: Option[];
  placeholder?: string;
};

export function Select({ className, id, options, placeholder, ...props }: SelectProps) {
  const { invalid, ...field } = useFieldProps(id);
  return (
    <select className={controlClass(invalid, cn("h-9 pr-8", className))} {...field} {...props}>
      {placeholder !== undefined && <option value="">{placeholder}</option>}
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

export function Checkbox({ label, description, className, ...props }: ComponentProps<"input"> & { label: ReactNode; description?: ReactNode }) {
  const id = useId();
  return (
    <div className={cn("flex items-start gap-2.5", className)}>
      <input
        id={id}
        type="checkbox"
        className="mt-0.5 size-4 shrink-0 rounded border-slate-300 accent-brand-600"
        {...props}
      />
      <label htmlFor={id} className="text-sm text-slate-700">
        {label}
        {description && <span className="block text-xs text-slate-500">{description}</span>}
      </label>
    </div>
  );
}

export function FilterSelect({
  label,
  value,
  onChange,
  options,
  allLabel,
  className,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  allLabel: string;
  className?: string;
}) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={controlClass(false, "h-9 pr-8")}
      >
        <option value="">{allLabel}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function FieldGroup({ label, hint, error, children }: { label: string; hint?: ReactNode; error?: string; children: ReactNode }) {
  const id = useId();
  return (
    <div role="group" aria-labelledby={`${id}-label`}>
      <p id={`${id}-label`} className="mb-1.5 text-sm font-medium text-slate-700">
        {label}
      </p>
      {children}
      {error ? (
        <p className="mt-1.5 text-sm text-red-700">{error}</p>
      ) : (
        hint && <p className="mt-1.5 text-xs text-slate-500">{hint}</p>
      )}
    </div>
  );
}
