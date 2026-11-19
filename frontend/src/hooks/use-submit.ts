"use client";

import { useState } from "react";
import { ApiError, errorMessage } from "@/lib/api";

export function useSubmit() {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function run<T>(request: () => Promise<T>, localErrors: Record<string, string> = {}): Promise<T | undefined> {
    if (Object.keys(localErrors).length > 0) {
      setFieldErrors(localErrors);
      setError("Please correct the highlighted fields.");
      return undefined;
    }
    setSaving(true);
    setError(null);
    setFieldErrors({});
    try {
      return await request();
    } catch (caught) {
      if (caught instanceof ApiError && caught.fieldErrors.length > 0) {
        setFieldErrors(caught.byField);
        const general = caught.fieldErrors.filter((item) => ["body", "query"].includes(item.field));
        setError(general.length ? general.map((item) => item.message).join(". ") : "Please correct the highlighted fields.");
      } else {
        setError(errorMessage(caught));
      }
      return undefined;
    } finally {
      setSaving(false);
    }
  }

  return { run, saving, error, fieldErrors };
}
