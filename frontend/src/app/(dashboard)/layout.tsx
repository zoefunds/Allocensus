"use client";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { DashboardNav } from "@/components/layout/DashboardNav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  useEffect(() => { if (!isAuthenticated) router.push("/login"); }, [isAuthenticated, router]);
  if (!isAuthenticated) return null;
  return (
    <div className="min-h-screen bg-background">
      <DashboardNav />
      <main className="ml-64 min-h-screen">
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
