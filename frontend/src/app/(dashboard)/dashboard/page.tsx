"use client";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI, rebalancingAPI } from "@/lib/api";
import { formatCurrency, statusLabel } from "@/lib/utils";
import { Card, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import Link from "next/link";
import { ArrowRight, TrendingUp, Briefcase, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis } from "recharts";

const mockHistory = [
  { date: "Jan", value: 18200000 }, { date: "Feb", value: 19100000 },
  { date: "Mar", value: 18700000 }, { date: "Apr", value: 21300000 },
  { date: "May", value: 22800000 }, { date: "Jun", value: 24800000 },
];

export default function DashboardPage() {
  const { data: portfoliosRes } = useQuery({ queryKey: ["portfolios"], queryFn: () => portfolioAPI.list() });
  const { data: proposalsRes } = useQuery({ queryKey: ["proposals"], queryFn: () => rebalancingAPI.list() });

  const portfolios = portfoliosRes?.data ?? [];
  const proposals = proposalsRes?.data ?? [];

  const totalAUM = portfolios.reduce((s: number, p: { total_value_usd: number }) => s + p.total_value_usd, 0);
  const approved = proposals.filter((p: { status: string }) => p.status === "approved").length;
  const pending = proposals.filter((p: { status: string }) => p.status === "pending_consensus").length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">Portfolio intelligence overview</p>
        </div>
        <Link href="/rebalancing/new" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-medium transition-colors">
          <RefreshCw className="w-4 h-4" /> New evaluation
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total AUM", value: formatCurrency(totalAUM), icon: TrendingUp, color: "emerald", change: "+4.2% this month" },
          { label: "Portfolios", value: portfolios.length, icon: Briefcase, color: "indigo", change: `${portfolios.length} active` },
          { label: "Evaluations", value: proposals.length, icon: RefreshCw, color: "emerald", change: `${approved} approved` },
          { label: "Pending consensus", value: pending, icon: CheckCircle, color: pending > 0 ? "amber" : "emerald", change: pending > 0 ? "In review" : "All resolved" },
        ].map(({ label, value, icon: Icon, color, change }) => (
          <Card key={label} className="metric-card">
            <div className="flex items-start justify-between mb-3">
              <div className={`w-9 h-9 rounded-xl bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center`}>
                <Icon className={`w-4 h-4 text-${color}-400`} />
              </div>
            </div>
            <p className="text-2xl font-bold text-foreground mb-0.5">{value}</p>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className={`text-xs text-${color}-400 mt-1`}>{change}</p>
          </Card>
        ))}
      </div>

      {/* AUM chart */}
      <Card>
        <CardTitle className="mb-6">Portfolio value over time</CardTitle>
        <ResponsiveContainer width="100%" height={180}>
          <AreaChart data={mockHistory}>
            <defs>
              <linearGradient id="aum" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(215 20% 55%)" }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "hsl(222 47% 7%)", border: "1px solid hsl(222 47% 14%)", borderRadius: 12, fontSize: 12 }}
              formatter={(v: number) => [formatCurrency(v), "AUM"]}
            />
            <Area type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} fill="url(#aum)" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* Recent proposals */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center justify-between mb-6">
            <CardTitle>Recent evaluations</CardTitle>
            <Link href="/rebalancing" className="text-xs text-muted-foreground hover:text-emerald-400 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {proposals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              <RefreshCw className="w-8 h-8 mx-auto mb-3 opacity-30" />
              No evaluations yet. Start by creating a portfolio rebalancing proposal.
            </div>
          ) : (
            <div className="space-y-3">
              {proposals.slice(0, 5).map((p: { id: string; status: string; created_at: string; portfolio_id: string }) => (
                <Link key={p.id} href={`/rebalancing/${p.id}`} className="flex items-center justify-between p-3 rounded-xl hover:bg-secondary/50 transition-colors">
                  <div>
                    <p className="text-sm font-medium font-mono">{p.id.slice(0, 8)}...</p>
                    <p className="text-xs text-muted-foreground">{new Date(p.created_at).toLocaleDateString()}</p>
                  </div>
                  <Badge variant={p.status === "approved" ? "success" : p.status === "rejected" ? "danger" : p.status === "pending_consensus" ? "warning" : "default"}>
                    {statusLabel(p.status)}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-6">
            <CardTitle>Portfolio health</CardTitle>
            <Link href="/portfolios" className="text-xs text-muted-foreground hover:text-emerald-400 flex items-center gap-1">
              Manage <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {portfolios.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              <Briefcase className="w-8 h-8 mx-auto mb-3 opacity-30" />
              No portfolios yet.
              <Link href="/portfolios" className="block text-emerald-400 mt-2">Create your first portfolio →</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {portfolios.slice(0, 4).map((p: { id: string; name: string; total_value_usd: number; is_active: boolean }) => (
                <Link key={p.id} href={`/portfolios/${p.id}`} className="flex items-center justify-between p-3 rounded-xl hover:bg-secondary/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                      <Briefcase className="w-3.5 h-3.5 text-indigo-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{p.name}</p>
                      <p className="text-xs text-muted-foreground">{formatCurrency(p.total_value_usd)}</p>
                    </div>
                  </div>
                  {p.is_active ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                  )}
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
