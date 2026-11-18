import type { Metadata } from "next";
import { Suspense } from "react";
import { FactoriesView } from "@/components/factories/factories-view";

export const metadata: Metadata = { title: "Factories" };

export default function FactoriesPage() {
  return (
    <Suspense>
      <FactoriesView />
    </Suspense>
  );
}
