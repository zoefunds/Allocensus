"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { portfolioAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const ASSET_CLASSES = ["Equities", "Fixed Income", "Alternatives", "Real Estate", "Commodities", "Cash", "Crypto"];

export default function NewPortfolioPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    aum: "",
    base_currency: "USD",
    investor_profile: "balanced",
    allowed_asset_classes: ["Equities", "Fixed Income"],
  });

  const toggleAsset = (asset: string) => {
    setForm(f => ({
      ...f,
      allowed_asset_classes: f.allowed_asset_classes.includes(asset)
        ? f.allowed_asset_classes.filter(a => a !== asset)
        : [...f.allowed_asset_classes, asset],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return toast.error("Portfolio name is required");
    if (!form.aum || Number(form.aum) <= 0) return toast.error("AUM must be a positive number");
    setLoading(true);
    try {
      await portfolioAPI.create({
        ...form,
        aum: Number(form.aum),
      });
      await queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      toast.success("Portfolio created");
      router.push("/portfolios");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to create portfolio";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/portfolios">
          <Button variant="ghost" size="sm"><ArrowLeft className="w-4 h-4" /> Back</Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">New Portfolio</h1>
          <p className="text-muted-foreground text-sm">Create an institutional portfolio for AI-validated rebalancing</p>
        </div>
      </div>

      <Card>
        <CardTitle className="mb-6">Portfolio Details</CardTitle>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Portfolio Name *</label>
            <input
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
              placeholder="e.g. Global Growth Fund"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Description</label>
            <textarea
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors resize-none"
              placeholder="Brief description of the portfolio strategy…"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">AUM (USD) *</label>
              <input
                type="number"
                min="0"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
                placeholder="25000000"
                value={form.aum}
                onChange={e => setForm(f => ({ ...f, aum: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Investor Profile</label>
              <select
                className="w-full bg-[#111118] border border-white/10 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                value={form.investor_profile}
                onChange={e => setForm(f => ({ ...f, investor_profile: e.target.value }))}
              >
                <option value="conservative">Conservative</option>
                <option value="balanced">Balanced</option>
                <option value="growth">Growth</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Allowed Asset Classes</label>
            <div className="flex flex-wrap gap-2">
              {ASSET_CLASSES.map(asset => (
                <button
                  key={asset}
                  type="button"
                  onClick={() => toggleAsset(asset)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                    form.allowed_asset_classes.includes(asset)
                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                      : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                  }`}
                >
                  {asset}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={loading} className="flex-1">
              {loading ? "Creating…" : "Create Portfolio"}
            </Button>
            <Link href="/portfolios">
              <Button type="button" variant="outline">Cancel</Button>
            </Link>
          </div>
        </form>
      </Card>
    </div>
  );
}
