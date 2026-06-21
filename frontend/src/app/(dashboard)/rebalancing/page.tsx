"use client";
import { useQuery } from "@tanstack/react-query";
import { rebalancingAPI } from "@/lib/api";
import { statusLabel } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { Plus, RefreshCw } from "lucide-react";
import type { Proposal } from "@/types";

const statusVariant = (s: string) => {
  const m: Record<string, "success" | "danger" | "warning" | "pending" | "default"> = {
    approved: "success", rejected: "danger", pending_consensus: "warning",
    submitted: "pending", draft: "default", failed: "danger",
  };
  return m[s] ?? "default";
};

export default function RebalancingPage() {
  const { data: res, isLoading } = useQuery({ queryKey: ["proposals"], queryFn: () => rebalancingAPI.list() });
  const proposals: Proposal[] = res?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Rebalancing</h1>
          <p className="text-muted-foreground text-sm mt-1">AI-evaluated portfolio rebalancing proposals</p>
        </div>
        <Link href="/rebalancing/new">
          <Button><Plus className="w-4 h-4" /> New proposal</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="glass rounded-2xl h-16 animate-pulse" />)}</div>
      ) : proposals.length === 0 ? (
        <Card className="text-center py-16">
          <RefreshCw className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-30" />
          <p className="text-muted-foreground mb-4">No rebalancing proposals yet.</p>
          <Link href="/rebalancing/new"><Button>Create first proposal</Button></Link>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-3 text-muted-foreground font-medium">Proposal ID</th>
                  <th className="pb-3 text-muted-foreground font-medium">Portfolio</th>
                  <th className="pb-3 text-muted-foreground font-medium">Status</th>
                  <th className="pb-3 text-muted-foreground font-medium">TX Hash</th>
                  <th className="pb-3 text-muted-foreground font-medium">Created</th>
                  <th className="pb-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {proposals.map((p) => (
                  <tr key={p.id} className="hover:bg-secondary/20 transition-colors">
                    <td className="py-3 font-mono text-xs text-muted-foreground">{p.id.slice(0, 12)}...</td>
                    <td className="py-3 text-xs font-mono">{p.portfolio_id.slice(0, 8)}...</td>
                    <td className="py-3"><Badge variant={statusVariant(p.status)}>{statusLabel(p.status)}</Badge></td>
                    <td className="py-3 font-mono text-xs text-muted-foreground">{p.genlayer_tx_hash ? `${p.genlayer_tx_hash.slice(0, 10)}...` : "—"}</td>
                    <td className="py-3 text-xs text-muted-foreground">{new Date(p.created_at).toLocaleDateString()}</td>
                    <td className="py-3 text-right">
                      <Link href={`/rebalancing/${p.id}`} className="text-xs text-emerald-400 hover:text-emerald-300">View →</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
