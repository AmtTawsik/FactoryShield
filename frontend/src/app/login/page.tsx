import type { Metadata } from "next";
import { Suspense } from "react";
import { Logo } from "@/components/shell/logo";
import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in" };

export default function LoginPage() {
  return (
    <div className="flex min-h-screen">
      <div className="hidden w-[44%] max-w-xl flex-col justify-between bg-brand-900 p-10 text-brand-100 lg:flex">
        <Logo inverted />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-white">
            Safety and compliance for garment factories
          </h2>
          <p className="mt-3 max-w-md text-sm leading-6 text-brand-200">
            Track inspections, incidents and corrective actions across your factories, and ask the assistant about
            Bangladesh labour law and safety rules.
          </p>
          <ul className="mt-8 space-y-3 text-sm">
            {[
              "Inspection scores and trends per factory",
              "Incident reporting with severity and status",
              "Corrective actions with due dates and overdue alerts",
            ].map((point) => (
              <li key={point} className="flex items-center gap-2.5">
                <span className="size-1.5 rounded-full bg-brand-300" aria-hidden="true" />
                {point}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-brand-300/80">FactoryShield</p>
      </div>

      <main className="flex flex-1 items-center justify-center bg-white px-4 py-12 sm:px-6">
        <div className="w-full max-w-sm">
          <Logo className="mb-8 lg:hidden" />
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">Sign in to your account</h1>
          <p className="mt-1 text-sm text-slate-500">Use the email and password given by your administrator.</p>
          <Suspense>
            <LoginForm />
          </Suspense>
        </div>
      </main>
    </div>
  );
}
