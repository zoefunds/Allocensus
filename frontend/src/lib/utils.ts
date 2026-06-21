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
