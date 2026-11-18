import { AppShell, SwrProvider } from "@/components/shell/app-shell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SwrProvider>
      <AppShell>{children}</AppShell>
    </SwrProvider>
  );
}
