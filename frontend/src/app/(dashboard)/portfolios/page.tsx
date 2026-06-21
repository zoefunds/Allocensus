"use client";
import { useQuery } from "@tanstack/react-query";
import { portfolioAPI } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { Plus, Briefcase, ArrowRight } from "lucide-react";
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
