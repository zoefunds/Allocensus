"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { rebalancingAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SubmitToGenlayerModal } from "@/components/rebalancing/SubmitToGenlayerModal";
import { FileText, Download, Zap, CheckCircle2, XCircle, ArrowLeft, ExternalLink, AlertTriangle, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

const PENDING_TIMEOUT_MS = 10 * 60 * 1000;

function statusVariant(s: string): "success"|"danger"|"warning"|"info"|"default" {
  return ({ approved:"success", rejected:"danger", pending_consensus:"warning",
            submitted:"info", draft:"default", failed:"danger" } as Record<string,"success"|"danger"|"warning"|"info"|"default">)[s] ?? "default";
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export default function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [now, setNow] = useState(Date.now());

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["proposal", id],
    queryFn:  async () => {
      try {
        const proposalRes = await rebalancingAPI.get(id);
        const proposalData = proposalRes.data;
        if (proposalData?.status === "pending_consensus" && proposalData?.genlayer_tx_hash) {
          const pollRes = await rebalancingAPI.pollResult(id);
          if (pollRes.data?.status !== "pending_consensus") {
            return rebalancingAPI.get(id);
          }
        }
        return proposalRes;
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 404) {
          const listRes = await rebalancingAPI.list();
          const match = (listRes.data || []).find((proposal: { id?: string }) => proposal.id === id);
          if (match) return { data: match };
        }
        throw err;
      }
    },
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    refetchInterval: (q) => q.state.data?.data?.status === "pending_consensus" ? 4000 : false,
    refetchIntervalInBackground: true,
  });

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 15000);
    return () => window.clearInterval(timer);
  }, []);

  const proposal  = data?.data;
  const rationale = proposal?.rationale;
  const isDraft   = proposal?.status === "draft";
  const isPending = proposal?.status === "pending_consensus";
  const isDone    = ["approved","rejected"].includes(proposal?.status ?? "");
  const isApproved = proposal?.status === "approved";
  const pendingAgeMs = proposal && isPending
    ? Math.max(0, now - Date.parse(proposal.created_at))
    : 0;
  const pendingTooLong = Boolean(isPending && pendingAgeMs > PENDING_TIMEOUT_MS);

  const handleExportPdf = async () => {
    try { const r = await rebalancingAPI.exportPdf(id); downloadBlob(r.data, `allocensus-${id.slice(0,8)}.pdf`); }
    catch { toast.error("PDF export failed"); }
  };
  const handleExportCsv = async () => {
    try { const r = await rebalancingAPI.exportCsv(id); downloadBlob(r.data, `allocensus-${id.slice(0,8)}.csv`); }
    catch { toast.error("CSV export failed"); }
  };
  const handleDelete = async () => {
    if (!confirm("Delete this proposal? This cannot be undone.")) return;
    try {
      await rebalancingAPI.delete(id);
      toast.success("Proposal deleted");
      qc.invalidateQueries({ queryKey: ["proposals"] });
      router.push("/rebalancing");
    } catch { toast.error("Failed to delete proposal"); }
  };

  const handleSuccess = (approved: boolean) => {
    toast.success(approved ? "Proposal approved!" : "Proposal rejected");
    refetch();
    qc.invalidateQueries({ queryKey: ["proposal", id] });
    qc.invalidateQueries({ queryKey: ["proposals"] });
  };

  if (isLoading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
  if (!proposal) return <div className="flex items-center justify-center min-h-screen text-muted-foreground">Proposal not found</div>;

  return (
    <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => router.back()} className="text-muted-foreground hover:text-foreground"><ArrowLeft className="w-5 h-5" /></button>
            <div>
              <h1 className="text-2xl font-bold">Rebalancing Proposal</h1>
              <p className="text-xs text-muted-foreground font-mono mt-0.5">{proposal.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={statusVariant(proposal.status)}>{proposal.status.replace("_"," ").toUpperCase()}</Badge>
            {isDone && <>
              <Button variant="secondary" size="sm" onClick={handleExportCsv}><Download className="w-3.5 h-3.5" /> CSV</Button>
              <Button variant="secondary" size="sm" onClick={handleExportPdf}><FileText className="w-3.5 h-3.5" /> PDF</Button>
              <Link href={`/rebalancing/${id}/claim`}>
                <Button variant="secondary" size="sm">Claim Refund</Button>
              </Link>
            </>}
            {isDraft && <>
              <Button onClick={() => setShowModal(true)}><Zap className="w-4 h-4" />Submit to Genlayer</Button>
            </>}
            {(isDraft || isPending) && (
              <Button variant="danger" size="sm" onClick={handleDelete}><Trash2 className="w-3.5 h-3.5" /></Button>
            )}
        {isPending && <Button variant="secondary" disabled>
              <div className="w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              Awaiting Consensus
            </Button>}
          </div>
        </div>

        {proposal.genlayer_tx_hash && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary/30 border border-border rounded-xl px-4 py-2.5">
            <ExternalLink className="w-3.5 h-3.5" />
            <span>On-chain TX:</span>
            <code className="font-mono text-emerald-400">{proposal.genlayer_tx_hash}</code>
            <a href={`https://explorer-studio.genlayer.com/tx/${proposal.genlayer_tx_hash}`} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300">View on explorer ↗</a>
          </div>
        )}

        {proposal.constraint_violations?.length > 0 && (
          <Card>
            <div className="flex items-center gap-2 mb-4"><AlertTriangle className="w-4 h-4 text-amber-400" /><CardTitle className="text-amber-400">Constraint Violations</CardTitle></div>
            <div className="space-y-2">
              {proposal.constraint_violations.map((v: { rule: string; message: string }, i: number) => (
                <div key={i} className="flex items-start gap-3 bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
                  <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">{v.rule}</span>
                  <span className="text-sm text-amber-200">{v.message}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardTitle className="mb-4 text-muted-foreground text-xs font-semibold uppercase tracking-wider">Current Allocations</CardTitle>
            <div className="space-y-2">
              {Object.entries(proposal.current_allocations || {}).sort((a,b)=>(b[1] as number)-(a[1] as number)).map(([sym,w]) => (
                <div key={sym} className="flex items-center justify-between">
                  <span className="text-sm font-mono">{sym}</span>
                  <span className="text-sm text-muted-foreground">{Number(w).toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <CardTitle className="mb-4 text-muted-foreground text-xs font-semibold uppercase tracking-wider">Proposed Allocations</CardTitle>
            <div className="space-y-2">
              {Object.entries(proposal.proposed_allocations || {}).sort((a,b)=>(b[1] as number)-(a[1] as number)).map(([sym,w]) => {
                const cur = Number((proposal.current_allocations || {})[sym] ?? 0);
                const delta = Number(w) - cur;
                return (
                  <div key={sym} className="flex items-center justify-between">
                    <span className="text-sm font-mono">{sym}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{Number(w).toFixed(2)}%</span>
                      {delta !== 0 && <span className={`text-xs ${delta>0?"text-emerald-400":"text-red-400"}`}>{delta>0?"+":""}{delta.toFixed(2)}%</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {rationale && (
          <Card glow={isApproved ? "green" : undefined}>
            <div className="flex items-center gap-3 mb-6">
              {isApproved ? <CheckCircle2 className="w-6 h-6 text-emerald-400" /> : <XCircle className="w-6 h-6 text-red-400" />}
              <div>
                <CardTitle>AI Evaluation Rationale</CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Genlayer validator consensus
                  {rationale.confidence_score ? ` · Confidence ${(rationale.confidence_score*100).toFixed(0)}%` : ""}
                  {rationale.diversification_score != null ? ` · Diversification ${rationale.diversification_score}/100` : ""}
                </p>
              </div>
            </div>

            {rationale.rationale_text && (
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap mb-6">{rationale.rationale_text}</p>
            )}

            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Risk Analysis",        text: rationale.risk_analysis },
                { label: "Constraint Analysis",  text: rationale.constraint_analysis },
                { label: "Liquidity Assessment", text: rationale.liquidity_assessment },
                { label: "Objective Alignment",  text: rationale.objective_alignment },
              ].filter(s=>s.text).map(({label,text}) => (
                <div key={label} className="bg-secondary/30 border border-border rounded-xl p-4">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">{label}</p>
                  <p className="text-sm leading-relaxed">{text}</p>
                </div>
              ))}
            </div>

            {(rationale.validator_consensus?.key_risks_introduced?.length > 0 || rationale.validator_consensus?.key_risks_mitigated?.length > 0) && (
              <div className="grid grid-cols-2 gap-4 mt-4">
                {rationale.validator_consensus.key_risks_introduced?.length > 0 && (
                  <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
                    <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">Risks Introduced</p>
                    <ul className="space-y-1">{rationale.validator_consensus.key_risks_introduced.map((r: string, i: number) => (
                      <li key={i} className="text-sm text-red-300 flex gap-2"><span>&bull;</span>{r}</li>
                    ))}</ul>
                  </div>
                )}
                {rationale.validator_consensus.key_risks_mitigated?.length > 0 && (
                  <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Risks Mitigated</p>
                    <ul className="space-y-1">{rationale.validator_consensus.key_risks_mitigated.map((r: string, i: number) => (
                      <li key={i} className="text-sm text-emerald-300 flex gap-2"><span>&bull;</span>{r}</li>
                    ))}</ul>
                  </div>
                )}
              </div>
            )}

            {rationale.validator_consensus?.recommendation && (
              <div className="mt-4 bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-4">
                <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Recommendation</p>
                <p className="text-sm text-indigo-200">{rationale.validator_consensus.recommendation}</p>
              </div>
            )}
          </Card>
        )}

        {isPending && !rationale && !pendingTooLong && (
          <Card>
            <div className="flex flex-col items-center py-12 gap-4">
              <div className="w-12 h-12 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              <p className="font-medium">Validators are reaching consensus</p>
              <p className="text-sm text-muted-foreground text-center max-w-sm">
                Multiple Genlayer validators are independently evaluating your proposal. The page updates as soon as consensus is confirmed.
              </p>
            </div>
          </Card>
        )}

        {pendingTooLong && (
          <Card>
            <div className="flex flex-col items-center py-12 gap-4">
              <div className="w-12 h-12 rounded-full border-2 border-amber-400/40 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <p className="font-medium">Consensus is taking longer than expected</p>
              <p className="text-sm text-muted-foreground text-center max-w-sm">
                We have not received a finalized contract result yet. You can keep this page open, or use refresh to check again.
              </p>
              <Button variant="secondary" onClick={() => refetch()}>
                Refresh status
              </Button>
            </div>
          </Card>
        )}
      {showModal && (
        <SubmitToGenlayerModal proposalId={id} onClose={() => setShowModal(false)} onSuccess={handleSuccess} />
      )}
    </div>
  );
}
