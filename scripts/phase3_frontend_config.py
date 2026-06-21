"""ALLOCENSUS — Phase 3 Frontend Config Files"""
import os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("frontend/package.json", json.dumps({
    "name": "allocensus-frontend",
    "version": "1.0.0",
    "private": True,
    "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start",
        "lint": "next lint",
        "type-check": "tsc --noEmit"
    },
    "dependencies": {
        "next": "15.0.3",
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "typescript": "^5",
        "@tanstack/react-query": "^5.61.0",
        "zustand": "^5.0.1",
        "axios": "^1.7.7",
        "recharts": "^2.13.3",
        "react-hook-form": "^7.53.2",
        "zod": "^3.23.8",
        "@hookform/resolvers": "^3.9.1",
        "framer-motion": "^11.11.11",
        "lucide-react": "^0.460.0",
        "clsx": "^2.1.1",
        "tailwind-merge": "^2.5.4",
        "date-fns": "^4.1.0",
        "react-hot-toast": "^2.4.1",
        "@radix-ui/react-dialog": "^1.1.2",
        "@radix-ui/react-dropdown-menu": "^2.1.2",
        "@radix-ui/react-select": "^2.1.2",
        "@radix-ui/react-tabs": "^1.1.1",
        "@radix-ui/react-tooltip": "^1.1.4",
        "@radix-ui/react-progress": "^1.1.0",
        "@radix-ui/react-separator": "^1.1.0",
        "@radix-ui/react-avatar": "^1.1.1",
        "@radix-ui/react-badge": "^1.0.0",
        "ethers": "^6.13.4",
        "next-themes": "^0.4.3",
        "react-intersection-observer": "^9.13.1"
    },
    "devDependencies": {
        "@types/node": "^20",
        "@types/react": "^19",
        "@types/react-dom": "^19",
        "autoprefixer": "^10.4.20",
        "postcss": "^8",
        "tailwindcss": "^3.4.14",
        "eslint": "^8",
        "eslint-config-next": "15.0.3"
    }
}, indent=2))

write("frontend/tsconfig.json", json.dumps({
    "compilerOptions": {
        "target": "ES2017",
        "lib": ["dom", "dom.iterable", "esnext"],
        "allowJs": True,
        "skipLibCheck": True,
        "strict": True,
        "noEmit": True,
        "esModuleInterop": True,
        "module": "esnext",
        "moduleResolution": "bundler",
        "resolveJsonModule": True,
        "isolatedModules": True,
        "jsx": "preserve",
        "incremental": True,
        "plugins": [{"name": "next"}],
        "paths": {"@/*": ["./src/*"]}
    },
    "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
    "exclude": ["node_modules"]
}, indent=2))

write("frontend/next.config.ts", '''\
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "plus.unsplash.com" },
      { protocol: "https", hostname: "assets.coingecko.com" },
    ],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
''')

write("frontend/tailwind.config.ts", '''\
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        emerald: {
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
        indigo: {
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out",
        "fade-in": "fadeIn 0.3s ease-out",
        pulse2: "pulse2 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        pulse2: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
''')

write("frontend/postcss.config.js", '''\
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
''')

write("frontend/.eslintrc.json", json.dumps({
    "extends": ["next/core-web-vitals", "next/typescript"]
}, indent=2))

# ── Types ──────────────────────────────────────────────────────────────────
write("frontend/src/types/index.ts", '''\
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "portfolio_manager" | "analyst";
  is_active: boolean;
  is_email_verified: boolean;
  wallet_address: string | null;
  created_at: string;
}

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  total_value_usd: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  assets: PortfolioAsset[];
}

export interface PortfolioAsset {
  id: string;
  symbol: string;
  name: string;
  asset_class: string;
  quantity: number;
  current_price_usd: number;
  current_value_usd: number;
  target_weight_pct: number;
  current_weight_pct: number;
}

export interface Proposal {
  id: string;
  portfolio_id: string;
  status: "draft" | "submitted" | "pending_consensus" | "approved" | "rejected" | "failed";
  current_allocations: Record<string, number>;
  proposed_allocations: Record<string, number>;
  constraint_violations: ConstraintViolation[];
  genlayer_tx_hash: string | null;
  notes: string | null;
  created_at: string;
  rationale?: Rationale;
}

export interface ConstraintViolation {
  rule: string;
  message: string;
  current_value: number;
  limit: number;
}

export interface Rationale {
  id: string;
  proposal_id: string;
  approved: boolean;
  confidence_score: number | null;
  rationale_text: string;
  risk_analysis: string | null;
  constraint_analysis: string | null;
  diversification_score: number | null;
  liquidity_assessment: string | null;
  objective_alignment: string | null;
  validator_consensus: Record<string, unknown>;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  on_chain_ref: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}
''')

# ── API client ─────────────────────────────────────────────────────────────
write("frontend/src/lib/api.ts", '''\
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: false,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_URL}/api/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post("/api/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),
  refresh: (refresh_token: string) =>
    api.post("/api/auth/refresh", { refresh_token }),
  verifyEmail: (token: string) =>
    api.post(`/api/auth/verify-email?token=${token}`),
};

// Portfolios
export const portfolioAPI = {
  list: () => api.get("/api/portfolios"),
  get: (id: string) => api.get(`/api/portfolios/${id}`),
  create: (data: unknown) => api.post("/api/portfolios", data),
  update: (id: string, data: unknown) => api.patch(`/api/portfolios/${id}`, data),
  delete: (id: string) => api.delete(`/api/portfolios/${id}`),
  getDrift: (id: string) => api.get(`/api/portfolios/${id}/drift`),
};

// Rebalancing
export const rebalancingAPI = {
  list: () => api.get("/api/rebalancing"),
  get: (id: string) => api.get(`/api/rebalancing/${id}`),
  create: (data: unknown) => api.post("/api/rebalancing", data),
  submit: (id: string) => api.post(`/api/rebalancing/${id}/submit`),
  pollResult: (id: string) => api.post(`/api/rebalancing/${id}/poll-result`),
  getRationale: (id: string) => api.get(`/api/rebalancing/${id}/rationale`),
};

// Users
export const userAPI = {
  me: () => api.get("/api/users/me"),
  update: (data: unknown) => api.patch("/api/users/me", data),
  wallet: () => api.get("/api/users/me/wallet"),
  exportKey: (password: string) => api.post("/api/users/me/wallet/export-key", { password }),
};

// Audit
export const auditAPI = {
  events: (params?: { limit?: number; event_type?: string }) =>
    api.get("/api/audit/events", { params }),
  compliance: () => api.get("/api/audit/compliance"),
};

// Admin
export const adminAPI = {
  stats: () => api.get("/api/admin/stats"),
  users: () => api.get("/api/admin/users"),
  updateRole: (userId: string, role: string) =>
    api.patch(`/api/admin/users/${userId}/role?role=${role}`),
};
''')

# ── Auth store ─────────────────────────────────────────────────────────────
write("frontend/src/stores/auth.ts", '''\
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  walletAddress: string | null;
  setAuth: (user: User, access: string, refresh: string, wallet?: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      walletAddress: null,
      isAuthenticated: false,
      setAuth: (user, access, refresh, wallet) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ user, accessToken: access, refreshToken: refresh, walletAddress: wallet ?? null, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, accessToken: null, refreshToken: null, walletAddress: null, isAuthenticated: false });
      },
    }),
    { name: "allocensus-auth", partialize: (s) => ({ user: s.user, accessToken: s.accessToken, refreshToken: s.refreshToken, walletAddress: s.walletAddress, isAuthenticated: s.isAuthenticated }) }
  )
);
''')

# ── Utils ──────────────────────────────────────────────────────────────────
write("frontend/src/lib/utils.ts", '''\
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
}

export function formatPct(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatAddress(addr: string): string {
  if (!addr) return "";
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    approved: "text-emerald-400",
    rejected: "text-red-400",
    pending_consensus: "text-amber-400",
    submitted: "text-blue-400",
    draft: "text-slate-400",
    failed: "text-red-500",
  };
  return map[status] ?? "text-slate-400";
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    approved: "Approved",
    rejected: "Rejected",
    pending_consensus: "In Review",
    submitted: "Submitted",
    draft: "Draft",
    failed: "Failed",
  };
  return map[status] ?? status;
}
''')

print("✅ Frontend config complete.")
