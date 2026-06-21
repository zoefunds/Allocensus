"use client";

import { useState } from "react";
import { ethers } from "ethers";
import { useGenlayerTx } from "@/hooks/useGenlayerTx";
import { userAPI } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Shield, Loader2, CheckCircle2, XCircle, ExternalLink, Lock, Zap } from "lucide-react";

interface Props {
  proposalId: string;
  onClose:    () => void;
  onSuccess:  (approved: boolean) => void;
}

const STATUS_LABELS: Record<string, string> = {
  idle:               "Ready",
  fetching_call_data: "Preparing transaction…",
  awaiting_signature: "Decrypting wallet…",
  broadcasting:       "Broadcasting to Genlayer…",
  pending_consensus:  "Waiting for validator consensus…",
  confirmed:          "Consensus reached!",
  failed:             "Transaction failed",
};

export function SubmitToGenlayerModal({ proposalId, onClose, onSuccess }: Props) {
  const [password, setPassword] = useState("");
  const [pwError,  setPwError]  = useState("");
  const { status, txHash, approved, error, submitProposal } = useGenlayerTx();

  const isProcessing = !["idle", "failed"].includes(status);
  const isDone       = status === "confirmed";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError("");

    let keystoreJson: string;
    try {
      const res = await userAPI.wallet();
      keystoreJson = res.data?.keystore_json;
      if (!keystoreJson) throw new Error("no keystore");
    } catch {
      setPwError("Could not load your wallet. Please try again.");
      return;
    }

    let decryptedKey: string;
    try {
      const wallet = await ethers.Wallet.fromEncryptedJson(keystoreJson, password);
      decryptedKey = wallet.privateKey;
    } catch {
      setPwError("Incorrect password. Please try again.");
      return;
    }

    await submitProposal(proposalId, decryptedKey);
    decryptedKey = "0".repeat(66);

    if (status === "confirmed" && approved !== null) {
      onSuccess(approved);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-2xl w-full max-w-md p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Zap className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Submit to Genlayer</h2>
            <p className="text-xs text-muted-foreground">AI validator consensus evaluation</p>
          </div>
        </div>

        <div className="flex gap-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4 mb-6">
          <Lock className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-emerald-300 leading-relaxed">
            Your password decrypts your wallet locally in your browser.
            Your private key and password are never transmitted to any server.
          </p>
        </div>

        {isProcessing || isDone ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 py-2">
              {isDone
                ? <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                : <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" />}
              <span className="text-sm font-medium">{STATUS_LABELS[status]}</span>
            </div>

            {txHash && (
              <div className="bg-secondary/50 rounded-xl p-3">
                <p className="text-xs text-muted-foreground mb-1">Transaction Hash</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs text-emerald-400 font-mono truncate flex-1">{txHash}</code>
                  <a href={`https://studio.genlayer.com/tx/${txHash}`} target="_blank"
                     rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground flex-shrink-0">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            )}

            {isDone && approved !== null && (
              <div className={`flex items-center gap-3 rounded-xl p-4 ${
                approved
                  ? "bg-emerald-500/10 border border-emerald-500/20"
                  : "bg-red-500/10 border border-red-500/20"
              }`}>
                {approved
                  ? <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  : <XCircle className="w-5 h-5 text-red-400" />}
                <div>
                  <p className={`font-bold ${approved ? "text-emerald-400" : "text-red-400"}`}>
                    {approved ? "Proposal Approved" : "Proposal Rejected"}
                  </p>
                  <p className="text-xs text-muted-foreground">Validator consensus reached</p>
                </div>
              </div>
            )}

            {status === "pending_consensus" && (
              <p className="text-xs text-muted-foreground text-center">
                Validators are independently evaluating your proposal.
                This typically takes 30–90 seconds.
              </p>
            )}

            <div className="flex gap-3 pt-2">
              {isDone ? (
                <Button variant="primary" className="flex-1"
                  onClick={() => { onSuccess(approved ?? false); onClose(); }}>
                  View Rationale
                </Button>
              ) : (
                <Button variant="secondary" className="flex-1" onClick={onClose}>
                  Close (running in background)
                </Button>
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Account Password"
              type="password"
              placeholder="Enter your password to sign the transaction"
              value={password}
              onChange={e => setPassword(e.target.value)}
              error={pwError}
              autoFocus
              required
            />

            {error && (
              <div className="flex items-start gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p className="text-xs">{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>Cancel</Button>
              <Button type="submit" variant="primary" className="flex-1" disabled={!password}>
                <Shield className="w-4 h-4" />
                Sign & Submit
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
