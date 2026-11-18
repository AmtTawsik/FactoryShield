import type { Metadata } from "next";
import Link from "next/link";
import { AuthLayout } from "@/components/shell/auth-layout";
import { RegisterForm } from "./register-form";

export const metadata: Metadata = { title: "Create an organization account" };

export default function RegisterPage() {
  return (
    <AuthLayout
      title="Create an organization account"
      description="For a company or factory group. You become its admin and can add factories and staff."
    >
      <RegisterForm />
      <p className="mt-8 border-t border-slate-200 pt-6 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-brand-700 hover:text-brand-800">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
