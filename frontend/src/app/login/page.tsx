import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { AuthLayout } from "@/components/shell/auth-layout";
import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in" };

export default function LoginPage() {
  return (
    <AuthLayout title="Sign in to your account" description="Use the email and password for your organization account.">
      <Suspense>
        <LoginForm />
      </Suspense>
      <p className="mt-8 border-t border-slate-200 pt-6 text-center text-sm text-slate-600">
        New to FactoryShield?{" "}
        <Link href="/register" className="font-medium text-brand-700 hover:text-brand-800">
          Create an organization account
        </Link>
      </p>
    </AuthLayout>
  );
}
