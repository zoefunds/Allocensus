"""ALLOCENSUS — Frontend Layout + Global CSS"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("frontend/src/app/globals.css", '''\
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 222 47% 5%;
    --foreground: 210 40% 98%;
    --card: 222 47% 7%;
    --card-foreground: 210 40% 98%;
    --primary: 160 84% 39%;
    --primary-foreground: 0 0% 100%;
    --secondary: 222 47% 11%;
    --secondary-foreground: 210 40% 98%;
    --muted: 222 47% 11%;
    --muted-foreground: 215 20% 55%;
    --accent: 246 70% 60%;
    --accent-foreground: 0 0% 100%;
    --border: 222 47% 14%;
    --input: 222 47% 11%;
    --ring: 160 84% 39%;
  }
}

@layer base {
  * { @apply border-border; }
  body {
    @apply bg-background text-foreground antialiased;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: hsl(var(--border)); border-radius: 2px; }
}

@layer utilities {
  .glass {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.06);
  }
  .glow-green {
    box-shadow: 0 0 20px rgba(16,185,129,0.15), 0 0 60px rgba(16,185,129,0.05);
  }
  .glow-indigo {
    box-shadow: 0 0 20px rgba(99,102,241,0.15), 0 0 60px rgba(99,102,241,0.05);
  }
  .text-gradient-green {
    background: linear-gradient(135deg, #10b981, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .text-gradient-indigo {
    background: linear-gradient(135deg, #6366f1, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .noise {
    position: relative;
  }
  .noise::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    opacity: 0.4;
    pointer-events: none;
    z-index: 0;
  }
  .metric-card {
    @apply glass rounded-2xl p-6 transition-all duration-300 hover:border-emerald-500/20;
  }
}
''')

write("frontend/src/app/layout.tsx", '''\
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/layout/Providers";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Allocensus — AI-Validated Portfolio Rebalancing", template: "%s | Allocensus" },
  description: "Institutional-grade portfolio rebalancing intelligence powered by Genlayer AI validators. Transparent, auditable, defensible investment rationale on-chain.",
  keywords: ["portfolio rebalancing", "AI", "institutional", "Genlayer", "blockchain", "investment"],
  openGraph: {
    type: "website",
    siteName: "Allocensus",
    title: "Allocensus — AI-Validated Portfolio Rebalancing",
    description: "Transparent, on-chain investment rationale for institutional portfolios.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
''')

write("frontend/src/components/layout/Providers.tsx", '''\
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 60_000, retry: 1 } }
  }));
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "hsl(222 47% 9%)",
            color: "hsl(210 40% 98%)",
            border: "1px solid hsl(222 47% 14%)",
            borderRadius: "12px",
            fontSize: "13px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
''')

# ── Shared UI components ────────────────────────────────────────────────────
write("frontend/src/components/ui/Button.tsx", '''\
import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

const variants = {
  primary: "bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-900/30",
  secondary: "bg-secondary hover:bg-secondary/80 text-foreground border border-border",
  ghost: "hover:bg-secondary/50 text-muted-foreground hover:text-foreground",
  danger: "bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20",
  outline: "border border-border hover:bg-secondary/50 text-foreground",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs rounded-lg",
  md: "px-4 py-2 text-sm rounded-xl",
  lg: "px-6 py-3 text-base rounded-xl",
  xl: "px-8 py-4 text-lg rounded-2xl",
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = "primary", size = "md", loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed select-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.2" />
          <path d="M22 12a10 10 0 01-10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        </svg>
      )}
      {children}
    </button>
  )
);
Button.displayName = "Button";
''')

write("frontend/src/components/ui/Input.tsx", '''\
import { cn } from "@/lib/utils";
import { type InputHTMLAttributes, forwardRef } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(
  ({ className, label, error, hint, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-medium text-muted-foreground">{label}</label>}
      <input
        ref={ref}
        className={cn(
          "w-full bg-secondary border border-border rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none transition-all",
          "focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30",
          error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
      {hint && !error && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
);
Input.displayName = "Input";
''')

write("frontend/src/components/ui/Card.tsx", '''\
import { cn } from "@/lib/utils";

interface CardProps { className?: string; children: React.ReactNode; glow?: "green" | "indigo" }

export function Card({ className, children, glow }: CardProps) {
  return (
    <div className={cn(
      "glass rounded-2xl p-6 transition-all duration-300",
      glow === "green" && "glow-green hover:border-emerald-500/30",
      glow === "indigo" && "glow-indigo hover:border-indigo-500/30",
      className
    )}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("mb-4", className)}>{children}</div>;
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return <h3 className={cn("text-lg font-semibold text-foreground", className)}>{children}</h3>;
}
''')

write("frontend/src/components/ui/Badge.tsx", '''\
import { cn } from "@/lib/utils";

const variants = {
  default: "bg-secondary text-muted-foreground border-border",
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  danger: "bg-red-500/10 text-red-400 border-red-500/20",
  info: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  pending: "bg-blue-500/10 text-blue-400 border-blue-500/20",
};

export function Badge({ variant = "default", children, className }: {
  variant?: keyof typeof variants;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border", variants[variant], className)}>
      {children}
    </span>
  );
}
''')

# ── Dashboard nav ──────────────────────────────────────────────────────────
write("frontend/src/components/layout/DashboardNav.tsx", '''\
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
''')

print("✅ Frontend layout complete.")
