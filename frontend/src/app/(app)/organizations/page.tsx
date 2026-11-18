import type { Metadata } from "next";
import { Suspense } from "react";
import { OrganizationsView } from "@/components/organizations/organizations-view";

export const metadata: Metadata = { title: "Organizations" };

export default function OrganizationsPage() {
  return (
    <Suspense>
      <OrganizationsView />
    </Suspense>
  );
}
