"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { portfolioAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { formatCurrency } from "@/lib/utils";
import { ArrowLeft, Pencil, Trash2, Check, X, Briefcase } from "lucide-react";
import toast from "react-hot-toast";
import Link from "next/link";
import type { Portfolio } from "@/types";

export default function PortfolioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => portfolioAPI.get(id),
  });
  const portfolio: Portfolio | undefined = data?.data;

  const startEdit = () => {
    setForm({ name: portfolio?.name ?? "", description: portfolio?.description ?? "" });
    setEditing(true);
  };

  const cancelEdit = () => setEditing(false);

  const saveEdit = async () => {
    if (!form.name.trim()) return toast.error("Name is required");
    setSaving(true);
    try {
      await portfolioAPI.update(id, { name: form.name.trim(), description: form.description.trim() || null });
      toast.success("Portfolio updated");
      qc.invalidateQueries({ queryKey: ["portfolio", id] });
      qc.invalidateQueries({ queryKey: ["portfolios"] });
      setEditing(false);
    } catch { toast.error("Failed to update portfolio"); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete "${portfolio?.name}"? This cannot be undone.`)) return;
    try {
      await portfolioAPI.delete(id);
      toast.success("Portfolio deleted");
      qc.invalidateQueries({ queryKey: ["portfolios"] });
      router.push("/portfolios");
    } catch { toast.error("Failed to delete portfolio"); }
  };

  if (isLoading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
  if (!portfolio) return (
    <div className="flex items-center justify-center min-h-screen text-muted-foreground">Portfolio not found</div>
  );

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">{portfolio.name}</h1>
              <p className="text-xs text-muted-foreground font-mono">{portfolio.id}</p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {!editing && (
            <>
              <Button variant="secondary" size="sm" onClick={startEdit}>
                <Pencil className="w-3.5 h-3.5" /> Edit
              </Button>
              <Button variant="danger" size="sm" onClick={handleDelete}>
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Edit form */}
      {editing ? (
        <Card>
          <CardTitle className="mb-4">Edit Portfolio</CardTitle>
          <div className="space-y-4">
            <Input
              label="Name"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              required
            />
            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">Description</label>
              <textarea
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-emerald-500 resize-none"
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              />
            </div>
            <div className="flex gap-3">
              <Button onClick={saveEdit} disabled={saving} className="flex-1">
                <Check className="w-4 h-4" /> {saving ? "Saving…" : "Save changes"}
              </Button>
              <Button variant="secondary" onClick={cancelEdit}>
                <X className="w-4 h-4" /> Cancel
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <Card>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">AUM</p>
              <p className="text-2xl font-bold">{formatCurrency(portfolio.total_value_usd)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Currency</p>
              <p className="font-semibold">{portfolio.currency ?? "USD"}</p>
            </div>
          </div>
          {portfolio.description && (
            <p className="text-sm text-muted-foreground mt-4 pt-4 border-t border-border">{portfolio.description}</p>
          )}
        </Card>
      )}

      <div className="flex justify-between items-center">
        <h2 className="font-semibold">Rebalancing Proposals</h2>
        <Link href={`/rebalancing/new`}>
          <Button size="sm">New Proposal</Button>
        </Link>
      </div>

      <p className="text-sm text-muted-foreground">
        View all proposals for this portfolio on the{" "}
        <Link href="/rebalancing" className="text-emerald-400 hover:underline">Rebalancing page</Link>.
      </p>
    </div>
  );
}
