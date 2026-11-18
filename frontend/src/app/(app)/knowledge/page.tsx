import type { Metadata } from "next";
import { Suspense } from "react";
import { KnowledgeView } from "@/components/knowledge/knowledge-view";

export const metadata: Metadata = { title: "Knowledge documents" };

export default function KnowledgePage() {
  return (
    <Suspense>
      <KnowledgeView />
    </Suspense>
  );
}
