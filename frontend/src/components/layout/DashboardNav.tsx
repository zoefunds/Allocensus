"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn, formatAddress } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth";
import {
  LayoutDashboard, Briefcase, RefreshCw, FileText,
  Shield, Settings, LogOut, ChevronRight, Zap
} from "lucide-react";

const nav = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/portfolios", icon: Briefcase, label: "Portfolios" },
  { href: "/rebalancing", icon: RefreshCw, label: "Rebalancing" },
  { href: "/audit", icon: FileText, label: "Audit Trail" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function DashboardNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, walletAddress, logout } = useAuthStore();

  const handleLogout = () => { logout(); router.push("/login"); };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 glass border-r border-border flex flex-col z-40">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Zap className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-foreground tracking-tight">ALLOCENSUS</div>
            <div className="text-xs text-muted-foreground">StudioNet</div>
          </div>
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href} className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
              active
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
            )}>
              <Icon className="w-4 h-4" />
              {label}
              {active && <ChevronRight className="w-3 h-3 ml-auto" />}
            </Link>
          );
        })}
        {user?.role === "admin" && (
          <Link href="/admin" className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
            pathname.startsWith("/admin")
              ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
              : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
          )}>
            <Shield className="w-4 h-4" />
            Admin
          </Link>
        )}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-xs font-bold text-emerald-400">
            {user?.full_name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.role?.replace("_", " ")}</p>
          </div>
        </div>
        {walletAddress && (
          <div className="px-3 py-2 rounded-lg bg-secondary/50 mb-2">
            <p className="text-xs text-muted-foreground">Wallet</p>
            <p className="text-xs font-mono text-emerald-400">{formatAddress(walletAddress)}</p>
          </div>
        )}
        <button onClick={handleLogout} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/5">
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
