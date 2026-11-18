import type { Metadata } from "next";
import { Suspense } from "react";
import { FactoryDetailView } from "@/components/factories/factory-detail-view";

export const metadata: Metadata = { title: "Factory details" };

export default function FactoryDetailPage() {
  return (
    <Suspense>
      <FactoryDetailView />
    </Suspense>
  );
}
