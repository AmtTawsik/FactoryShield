import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/cn";

export function Logo({ className, inverted = false }: { className?: string; inverted?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span
        className={cn(
          "flex size-8 items-center justify-center rounded-md",
          inverted ? "bg-white/10 text-white" : "bg-brand-600 text-white",
        )}
      >
        <ShieldCheck className="size-5" aria-hidden="true" />
      </span>
      <span className={cn("text-base font-semibold tracking-tight", inverted ? "text-white" : "text-slate-900")}>
        FactoryShield
      </span>
    </span>
  );
}
