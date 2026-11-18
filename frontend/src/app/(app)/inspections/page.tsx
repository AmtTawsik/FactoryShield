import type { Metadata } from "next";
import { Suspense } from "react";
import { InspectionsView } from "@/components/inspections/inspections-view";

export const metadata: Metadata = { title: "Safety inspections" };

export default function InspectionsPage() {
  return (
    <Suspense>
      <InspectionsView />
    </Suspense>
  );
}
