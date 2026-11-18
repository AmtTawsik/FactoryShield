import type { Metadata } from "next";
import { Suspense } from "react";
import { ActionsView } from "@/components/actions/actions-view";

export const metadata: Metadata = { title: "Corrective actions" };

export default function ActionsPage() {
  return (
    <Suspense>
      <ActionsView />
    </Suspense>
  );
}
