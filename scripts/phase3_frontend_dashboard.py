"""ALLOCENSUS — Dashboard layout + main app pages"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("frontend/src/app/(dashboard)/layout.tsx", '''\
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
''')

write("frontend/src/app/(dashboard)/dashboard/page.tsx", '''\
"use client";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI, rebalancingAPI } from "@/lib/api";
import { formatCurrency, statusColor, statusLabel } from "@/lib/utils";
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
''')

write("frontend/src/app/(dashboard)/portfolios/page.tsx", '''\
"use client";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { Plus, Briefcase, TrendingUp, ArrowRight } from "lucide-react";
import type { Portfolio } from "@/types";

export default function PortfoliosPage() {
  const { data: res, isLoading } = useQuery({ queryKey: ["portfolios"], queryFn: () => portfolioAPI.list() });
  const portfolios: Portfolio[] = res?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Portfolios</h1>
          <p className="text-muted-foreground text-sm mt-1">{portfolios.length} active portfolio{portfolios.length !== 1 ? "s" : ""}</p>
        </div>
        <Link href="/portfolios/new">
          <Button size="md"><Plus className="w-4 h-4" /> New portfolio</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <div key={i} className="glass rounded-2xl h-48 animate-pulse" />)}
        </div>
      ) : portfolios.length === 0 ? (
        <Card className="text-center py-16">
          <Briefcase className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-30" />
          <p className="text-muted-foreground mb-4">No portfolios yet. Create your first to start AI-validated rebalancing.</p>
          <Link href="/portfolios/new"><Button>Create portfolio</Button></Link>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {portfolios.map((p) => (
            <Link key={p.id} href={`/portfolios/${p.id}`}>
              <Card className="hover:border-emerald-500/20 transition-all cursor-pointer group h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                    <Briefcase className="w-5 h-5 text-indigo-400" />
                  </div>
                  <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-emerald-400 transition-colors" />
                </div>
                <h3 className="font-semibold mb-1">{p.name}</h3>
                {p.description && <p className="text-xs text-muted-foreground mb-4 line-clamp-2">{p.description}</p>}
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground">Total value</p>
                    <p className="font-semibold text-foreground">{formatCurrency(p.total_value_usd)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Assets</p>
                    <p className="font-semibold">{p.assets?.length ?? 0}</p>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
''')

write("frontend/src/app/(dashboard)/rebalancing/page.tsx", '''\
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
''')

write("frontend/src/app/(dashboard)/rebalancing/[id]/page.tsx", '''\
"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rebalancingAPI } from "@/lib/api";
import { statusLabel } from "@/lib/utils";
import { Card, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import { CheckCircle, XCircle, Clock, Loader2, ExternalLink } from "lucide-react";
import type { Proposal, Rationale } from "@/types";

export default function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const { data: pRes } = useQuery({ queryKey: ["proposal", id], queryFn: () => rebalancingAPI.get(id) });
  const { data: rRes } = useQuery({ queryKey: ["rationale", id], queryFn: () => rebalancingAPI.getRationale(id), enabled: !!id, retry: false });

  const proposal: Proposal | undefined = pRes?.data;
  const rationale: Rationale | undefined = rRes?.data;

  const submitMutation = useMutation({
    mutationFn: () => rebalancingAPI.submit(id),
    onSuccess: () => { toast.success("Submitted to Genlayer validators!"); qc.invalidateQueries({ queryKey: ["proposal", id] }); },
    onError: () => toast.error("Submission failed"),
  });

  const pollMutation = useMutation({
    mutationFn: () => rebalancingAPI.pollResult(id),
    onSuccess: (res) => {
      if (res.data.status === "pending") toast("Validators still processing...");
      else { toast.success(`Result: ${res.data.approved ? "APPROVED" : "REJECTED"}`); qc.invalidateQueries({ queryKey: ["proposal", id] }); }
    },
  });

  if (!proposal) return <div className="text-muted-foreground">Loading...</div>;

  const statusVariant = (s: string) => {
    const m: Record<string, "success" | "danger" | "warning" | "pending" | "default"> = {
      approved: "success", rejected: "danger", pending_consensus: "warning",
      submitted: "pending", draft: "default", failed: "danger",
    };
    return m[s] ?? "default";
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Rebalancing Proposal</h1>
          <p className="text-muted-foreground text-xs mt-1 font-mono">{id}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={statusVariant(proposal.status)} className="text-sm px-4 py-1.5">{statusLabel(proposal.status)}</Badge>
          {proposal.status === "draft" && (
            <Button onClick={() => submitMutation.mutate()} loading={submitMutation.isPending}>
              Submit to Genlayer
            </Button>
          )}
          {proposal.status === "pending_consensus" && (
            <Button variant="secondary" onClick={() => pollMutation.mutate()} loading={pollMutation.isPending}>
              <Loader2 className="w-4 h-4 animate-spin" /> Check result
            </Button>
          )}
        </div>
      </div>

      {/* TX Hash */}
      {proposal.genlayer_tx_hash && (
        <div className="flex items-center gap-2 px-4 py-3 glass rounded-xl border border-border">
          <ExternalLink className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">On-chain TX:</span>
          <span className="text-xs font-mono text-emerald-400">{proposal.genlayer_tx_hash}</span>
        </div>
      )}

      {/* Allocations comparison */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardTitle className="mb-4">Current allocation</CardTitle>
          <div className="space-y-2">
            {Object.entries(proposal.current_allocations).map(([symbol, pct]) => (
              <div key={symbol} className="flex items-center justify-between text-sm">
                <span className="font-mono text-muted-foreground">{symbol}</span>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${Math.min(pct as number, 100)}%` }} />
                  </div>
                  <span className="text-xs w-12 text-right">{(pct as number).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <CardTitle className="mb-4">Proposed allocation</CardTitle>
          <div className="space-y-2">
            {Object.entries(proposal.proposed_allocations).map(([symbol, pct]) => (
              <div key={symbol} className="flex items-center justify-between text-sm">
                <span className="font-mono text-muted-foreground">{symbol}</span>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(pct as number, 100)}%` }} />
                  </div>
                  <span className="text-xs w-12 text-right">{(pct as number).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Constraint violations */}
      {proposal.constraint_violations.length > 0 && (
        <Card>
          <CardTitle className="mb-4 text-red-400">Constraint violations</CardTitle>
          <div className="space-y-2">
            {proposal.constraint_violations.map((v) => (
              <div key={v.rule} className="flex items-start gap-3 p-3 rounded-xl bg-red-500/5 border border-red-500/10">
                <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-red-400">{v.rule}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{v.message}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* AI Rationale */}
      {rationale ? (
        <Card glow={rationale.approved ? "green" : undefined}>
          <div className="flex items-center justify-between mb-6">
            <CardTitle>AI Rationale</CardTitle>
            <div className="flex items-center gap-2">
              {rationale.approved ? (
                <><CheckCircle className="w-5 h-5 text-emerald-400" /><span className="text-emerald-400 font-semibold">APPROVED</span></>
              ) : (
                <><XCircle className="w-5 h-5 text-red-400" /><span className="text-red-400 font-semibold">REJECTED</span></>
              )}
              {rationale.confidence_score !== null && (
                <span className="text-xs text-muted-foreground ml-2">Confidence: {((rationale.confidence_score ?? 0) * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">Overall rationale</h4>
              <p className="text-sm leading-relaxed">{rationale.rationale_text}</p>
            </div>
            {rationale.risk_analysis && (
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">Risk analysis</h4>
                <p className="text-sm leading-relaxed">{rationale.risk_analysis}</p>
              </div>
            )}
            {rationale.constraint_analysis && (
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">Constraint analysis</h4>
                <p className="text-sm leading-relaxed">{rationale.constraint_analysis}</p>
              </div>
            )}
            <div className="grid md:grid-cols-3 gap-4 pt-4 border-t border-border">
              {rationale.diversification_score !== null && (
                <div className="glass rounded-xl p-4">
                  <p className="text-xs text-muted-foreground mb-1">Diversification score</p>
                  <p className="text-2xl font-bold text-foreground">{rationale.diversification_score}<span className="text-sm text-muted-foreground">/100</span></p>
                </div>
              )}
              {rationale.liquidity_assessment && (
                <div className="glass rounded-xl p-4 col-span-2">
                  <p className="text-xs text-muted-foreground mb-1">Liquidity assessment</p>
                  <p className="text-sm">{rationale.liquidity_assessment}</p>
                </div>
              )}
            </div>
            {rationale.objective_alignment && (
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">Objective alignment</h4>
                <p className="text-sm leading-relaxed">{rationale.objective_alignment}</p>
              </div>
            )}
          </div>
        </Card>
      ) : (
        proposal.status === "pending_consensus" && (
          <Card className="text-center py-12">
            <Loader2 className="w-8 h-8 mx-auto mb-4 text-emerald-400 animate-spin" />
            <p className="text-muted-foreground">Genlayer validators are evaluating this proposal.</p>
            <p className="text-xs text-muted-foreground mt-1">Click &quot;Check result&quot; to poll for updates.</p>
          </Card>
        )
      )}
    </div>
  );
}
''')

write("frontend/src/app/(dashboard)/audit/page.tsx", '''\
"use client";
import { useQuery } from "@tanstack/react-query";
import { auditAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { FileText, ExternalLink } from "lucide-react";
import type { AuditEvent } from "@/types";

export default function AuditPage() {
  const { data: res } = useQuery({ queryKey: ["audit"], queryFn: () => auditAPI.events({ limit: 100 }) });
  const events: AuditEvent[] = res?.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Trail</h1>
        <p className="text-muted-foreground text-sm mt-1">Immutable record of all account and portfolio actions</p>
      </div>
      <Card>
        <CardTitle className="mb-6">Event log ({events.length})</CardTitle>
        {events.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
            No events yet.
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((e) => (
              <div key={e.id} className="flex items-start gap-4 p-3 rounded-xl hover:bg-secondary/30 transition-colors">
                <div className="w-2 h-2 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-medium text-foreground">{e.event_type}</span>
                    {e.resource_id && <span className="text-xs text-muted-foreground font-mono">{e.resource_id.slice(0, 16)}...</span>}
                  </div>
                  {e.on_chain_ref && (
                    <div className="flex items-center gap-1 mt-0.5">
                      <ExternalLink className="w-3 h-3 text-emerald-400" />
                      <span className="text-xs font-mono text-emerald-400">{e.on_chain_ref}</span>
                    </div>
                  )}
                </div>
                <span className="text-xs text-muted-foreground flex-shrink-0">{new Date(e.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
''')

write("frontend/src/app/(dashboard)/settings/page.tsx", '''\
"use client";
import { useAuthStore } from "@/stores/auth";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { formatAddress } from "@/lib/utils";
import { useState } from "react";
import { userAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Input } from "@/components/ui/Input";
import { Eye, EyeOff, Copy } from "lucide-react";

export default function SettingsPage() {
  const { user, walletAddress } = useAuthStore();
  const [exportPassword, setExportPassword] = useState("");
  const [exportedKey, setExportedKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const res = await userAPI.exportKey(exportPassword);
      setExportedKey(res.data.private_key);
      toast.success("Private key exported. Store it securely.");
    } catch {
      toast.error("Incorrect password");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardTitle className="mb-4">Account</CardTitle>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Name</span>
            <span>{user?.full_name}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Email</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Role</span>
            <span className="capitalize">{user?.role?.replace("_", " ")}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-muted-foreground">Email verified</span>
            <span className={user?.is_email_verified ? "text-emerald-400" : "text-amber-400"}>
              {user?.is_email_verified ? "Verified" : "Pending"}
            </span>
          </div>
        </div>
      </Card>

      <Card>
        <CardTitle className="mb-4">Blockchain Wallet</CardTitle>
        <div className="space-y-4">
          <div className="p-4 bg-secondary/50 rounded-xl">
            <p className="text-xs text-muted-foreground mb-1">Wallet address (StudioNet)</p>
            <div className="flex items-center gap-2">
              <p className="font-mono text-sm text-emerald-400">{walletAddress ?? "Not found"}</p>
              {walletAddress && (
                <button onClick={() => { navigator.clipboard.writeText(walletAddress); toast.success("Copied!"); }}>
                  <Copy className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium">Export private key</p>
            <p className="text-xs text-muted-foreground">Enter your account password to decrypt and export your private key. Store it in a hardware wallet or cold storage immediately.</p>
            <Input
              type="password"
              placeholder="Your account password"
              value={exportPassword}
              onChange={e => setExportPassword(e.target.value)}
            />
            <Button variant="outline" onClick={handleExport} loading={exporting} disabled={!exportPassword}>
              Export private key
            </Button>

            {exportedKey && (
              <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-red-400 font-medium">PRIVATE KEY — Store securely and never share</p>
                  <button onClick={() => setShowKey(!showKey)}>
                    {showKey ? <EyeOff className="w-4 h-4 text-muted-foreground" /> : <Eye className="w-4 h-4 text-muted-foreground" />}
                  </button>
                </div>
                {showKey ? (
                  <p className="font-mono text-xs break-all text-red-300">{exportedKey}</p>
                ) : (
                  <p className="font-mono text-xs text-muted-foreground">••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••</p>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
''')

print("✅ Dashboard pages complete.")
