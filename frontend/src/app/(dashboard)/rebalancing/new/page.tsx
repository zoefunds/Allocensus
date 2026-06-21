"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI, rebalancingAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import type { Portfolio } from "@/types";

interface AllocationRow {
  asset_class: string;
  current_pct: string;
  proposed_pct: string;
}

const ASSET_CLASSES = [
  "Equities", "Fixed Income", "Alternatives",
  "Real Estate", "Commodities", "Cash", "Crypto",
];

export default function NewProposalPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState("");
  const [notes, setNotes] = useState("");
  const [marketContext, setMarketContext] = useState({
    volatility_indicator: "",
    macro_signals: "",
    market_regime: "",
    additional_context: "",
  });
  const [rows, setRows] = useState<AllocationRow[]>([
    { asset_class: "Equities", current_pct: "65", proposed_pct: "55" },
    { asset_class: "Fixed Income", current_pct: "20", proposed_pct: "30" },
    { asset_class: "Alternatives", current_pct: "10", proposed_pct: "10" },
    { asset_class: "Cash", current_pct: "5", proposed_pct: "5" },
  ]);

  const { data: res } = useQuery({ queryKey: ["portfolios"], queryFn: () => portfolioAPI.list() });
  const portfolios: Portfolio[] = res?.data ?? [];

  const addRow = () =>
    setRows(r => [...r, { asset_class: "Equities", current_pct: "0", proposed_pct: "0" }]);

  const removeRow = (i: number) => setRows(r => r.filter((_, idx) => idx !== i));

  const updateRow = (i: number, field: keyof AllocationRow, value: string) =>
    setRows(r => r.map((row, idx) => idx === i ? { ...row, [field]: value } : row));

  const currentTotal = rows.reduce((s, r) => s + (Number(r.current_pct) || 0), 0);
  const proposedTotal = rows.reduce((s, r) => s + (Number(r.proposed_pct) || 0), 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolio) return toast.error("Select a portfolio");
    if (Math.abs(currentTotal - 100) > 0.01) return toast.error(`Current allocations must sum to 100% (currently ${currentTotal}%)`);
    if (Math.abs(proposedTotal - 100) > 0.01) return toast.error(`Proposed allocations must sum to 100% (currently ${proposedTotal}%)`);

    const proposed_allocations: Record<string, number> = {};
    const current_allocations: Record<string, number> = {};
    for (const row of rows) {
      if (!row.asset_class) continue;
      proposed_allocations[row.asset_class] = Number(row.proposed_pct);
      current_allocations[row.asset_class] = Number(row.current_pct);
    }

    setLoading(true);
    try {
      const res = await rebalancingAPI.create({
        portfolio_id: selectedPortfolio,
        current_allocations,
        proposed_allocations,
        notes,
        market_context: {
          volatility_indicator: marketContext.volatility_indicator || undefined,
          macro_signals: marketContext.macro_signals || undefined,
          market_regime: marketContext.market_regime || undefined,
          additional_context: marketContext.additional_context || undefined,
        },
      });
      toast.success("Proposal created — ready for Genlayer evaluation");
      router.push(`/rebalancing/${res.data.id}`);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string | { msg: string }[] } } })?.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map(d => d.msg).join(", ") : (detail ?? "Failed to create proposal");
      toast.error(String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/rebalancing">
          <Button variant="ghost" size="sm"><ArrowLeft className="w-4 h-4" /> Back</Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">New Rebalancing Proposal</h1>
          <p className="text-muted-foreground text-sm">Submit for AI-validation via Genlayer consensus</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Portfolio selection */}
        <Card>
          <CardTitle className="mb-4">Portfolio</CardTitle>
          <select
            required
            className="w-full bg-[#111118] border border-white/10 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-emerald-500 transition-colors"
            value={selectedPortfolio}
            onChange={e => setSelectedPortfolio(e.target.value)}
          >
            <option value="">— Select a portfolio —</option>
            {portfolios.map((p: Portfolio) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          {portfolios.length === 0 && (
            <p className="text-sm text-gray-500 mt-2">
              No portfolios yet.{" "}
              <Link href="/portfolios/new" className="text-emerald-400 hover:underline">Create one first.</Link>
            </p>
          )}
        </Card>

        {/* Allocations */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Allocations</CardTitle>
            <button type="button" onClick={addRow} className="flex items-center gap-1 text-sm text-emerald-400 hover:text-emerald-300">
              <Plus className="w-4 h-4" /> Add row
            </button>
          </div>

          <div className="grid grid-cols-[1fr_120px_120px_32px] gap-2 text-xs text-gray-400 mb-2 px-1">
            <span>Asset class</span>
            <span className="text-center">Current %</span>
            <span className="text-center">Proposed %</span>
            <span />
          </div>

          <div className="space-y-2">
            {rows.map((row, i) => (
              <div key={i} className="grid grid-cols-[1fr_120px_120px_32px] gap-2 items-center">
                <select
                  className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={row.asset_class}
                  onChange={e => updateRow(i, "asset_class", e.target.value)}
                >
                  {ASSET_CLASSES.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
                <input
                  type="number" min="0" max="100" step="0.1"
                  className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-white text-sm text-center focus:outline-none focus:border-emerald-500"
                  value={row.current_pct}
                  onChange={e => updateRow(i, "current_pct", e.target.value)}
                />
                <input
                  type="number" min="0" max="100" step="0.1"
                  className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-white text-sm text-center focus:outline-none focus:border-emerald-500"
                  value={row.proposed_pct}
                  onChange={e => updateRow(i, "proposed_pct", e.target.value)}
                />
                <button type="button" onClick={() => removeRow(i)} className="text-gray-500 hover:text-red-400 flex items-center justify-center">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-[1fr_120px_120px_32px] gap-2 mt-3 pt-3 border-t border-white/10 text-sm font-medium px-1">
            <span className="text-gray-400">Total</span>
            <span className={`text-center ${Math.abs(currentTotal - 100) > 0.01 ? "text-red-400" : "text-emerald-400"}`}>
              {currentTotal.toFixed(1)}%
            </span>
            <span className={`text-center ${Math.abs(proposedTotal - 100) > 0.01 ? "text-red-400" : "text-emerald-400"}`}>
              {proposedTotal.toFixed(1)}%
            </span>
            <span />
          </div>
        </Card>

        {/* Market context */}
        <Card>
          <CardTitle className="mb-4">Market Context <span className="text-gray-500 font-normal text-sm">(optional)</span></CardTitle>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Volatility indicator</label>
                <select
                  className="w-full bg-[#111118] border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={marketContext.volatility_indicator}
                  onChange={e => setMarketContext(m => ({ ...m, volatility_indicator: e.target.value }))}
                >
                  <option value="">— Select —</option>
                  <option value="low">Low (&lt;15)</option>
                  <option value="moderate">Moderate (15–25)</option>
                  <option value="high">High (25–35)</option>
                  <option value="extreme">Extreme (&gt;35)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Market regime</label>
                <select
                  className="w-full bg-[#111118] border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={marketContext.market_regime}
                  onChange={e => setMarketContext(m => ({ ...m, market_regime: e.target.value }))}
                >
                  <option value="">— Select —</option>
                  <option value="bull">Bull market</option>
                  <option value="bear">Bear market</option>
                  <option value="sideways">Sideways / range-bound</option>
                  <option value="recovery">Recovery</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Macro signals</label>
              <input
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                placeholder="e.g. Fed rate hold expected, inflation cooling"
                value={marketContext.macro_signals}
                onChange={e => setMarketContext(m => ({ ...m, macro_signals: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Additional context / justification</label>
              <textarea
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-emerald-500 resize-none"
                placeholder="Explain the rationale for this rebalancing…"
                value={marketContext.additional_context}
                onChange={e => setMarketContext(m => ({ ...m, additional_context: e.target.value }))}
              />
            </div>
          </div>
        </Card>

        {/* Notes */}
        <Card>
          <CardTitle className="mb-3">Internal Notes <span className="text-gray-500 font-normal text-sm">(optional)</span></CardTitle>
          <textarea
            rows={2}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-emerald-500 resize-none"
            placeholder="Notes for internal review…"
            value={notes}
            onChange={e => setNotes(e.target.value)}
          />
        </Card>

        <div className="flex gap-3">
          <Button type="submit" disabled={loading} className="flex-1">
            {loading ? "Creating proposal…" : "Create Proposal"}
          </Button>
          <Link href="/rebalancing">
            <Button type="button" variant="outline">Cancel</Button>
          </Link>
        </div>

        <p className="text-xs text-gray-500 text-center">
          After creation you&apos;ll be taken to the proposal page where you can sign and submit to Genlayer for on-chain AI validation.
        </p>
      </form>
    </div>
  );
}
