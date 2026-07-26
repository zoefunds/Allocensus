"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ethers } from "ethers";
import { useQuery } from "@tanstack/react-query";
import { abi as glAbi } from "genlayer-js";
import { rebalancingAPI, userAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuthStore } from "@/stores/auth";
import toast from "react-hot-toast";
import { ArrowLeft, CheckCircle2, Loader2, Shield, ExternalLink } from "lucide-react";

const CONSENSUS_MAIN_CONTRACT = "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575";
const CLAIM_ABI = [
  {
    type: "function",
    name: "addTransaction",
    stateMutability: "nonpayable",
    inputs: [
      { name: "_sender", type: "address" },
      { name: "_recipient", type: "address" },
      { name: "_numOfInitialValidators", type: "uint256" },
      { name: "_maxRotations", type: "uint256" },
      { name: "_txData", type: "bytes" },
    ],
    outputs: [],
  },
] as const;

export default function ClaimStakePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { walletPassword } = useAuthStore();
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "done" | "error">("idle");
  const [txHash, setTxHash] = useState("");
  const [error, setError] = useState("");

  const { data } = useQuery({ queryKey: ["proposal-stake", id], queryFn: () => rebalancingAPI.stake(id) });
  const stake = data?.data;

  const submitClaim = async () => {
    setError("");
    setStatus("submitting");
    try {
      const keystoreRes = await userAPI.wallet();
      const keystoreJson = keystoreRes.data?.keystore_json;
      if (!keystoreJson) throw new Error("Wallet keystore unavailable");

      const w = await ethers.Wallet.fromEncryptedJson(keystoreJson, walletPassword || password);
      const provider = new ethers.JsonRpcProvider(process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "https://studio.genlayer.com/api");

      const calldataObj = glAbi.calldata.makeCalldataObject("claim_stake_refund", [], {
        proposal_id: id,
        recipient_address: w.address,
      });
      const encodedCalldata = glAbi.calldata.encode(calldataObj);
      const serializedData = glAbi.transactions.serialize([encodedCalldata, false]);
      const iface = new ethers.Interface(CLAIM_ABI);
      const encodedCall = iface.encodeFunctionData("addTransaction", [
        w.address,
        stake?.contract_address || process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS || "",
        BigInt(5),
        BigInt(3),
        serializedData,
      ]);
      const tx = await w.connect(provider).sendTransaction({
        to: CONSENSUS_MAIN_CONTRACT,
        data: encodedCall,
        gasPrice: BigInt(0),
        gasLimit: BigInt(1_000_000),
      });
      setTxHash(tx.hash);
      await tx.wait();
      setStatus("done");
      toast.success("Claim submitted");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : String(e));
      toast.error("Claim failed");
    }
  };

  useEffect(() => {
    if (walletPassword && status === "idle" && stake?.claimable) {
      void submitClaim();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [walletPassword, stake?.claimable]);

  return (
    <div className="max-w-2xl space-y-6">
      <button onClick={() => router.back()} className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-2">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <Card>
        <CardTitle className="mb-4">Claim Stake Refund</CardTitle>
        <div className="space-y-4 text-sm">
          <p className="text-muted-foreground">Users stake exactly 1 GEN to submit a rebalance. After the request is processed, you can claim back 50% of that stake.</p>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-secondary/50">Stake: <span className="font-mono text-emerald-400">{stake?.stake_wei ? `${Number(stake.stake_wei) / 1e18} GEN` : "—"}</span></div>
            <div className="p-3 rounded-xl bg-secondary/50">Refund: <span className="font-mono text-emerald-400">{stake?.refund_wei ? `${Number(stake.refund_wei) / 1e18} GEN` : "—"}</span></div>
          </div>
          {txHash && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="font-mono text-emerald-400 break-all">{txHash}</span>
            </div>
          )}
          {status === "error" && <p className="text-red-400 text-xs">{error}</p>}
          {!stake?.claimable ? (
            <p className="text-amber-400 text-sm">This claim is not available yet.</p>
          ) : (
            <div className="space-y-3">
              {!walletPassword && (
                <Input
                  label="Account password"
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter password to decrypt wallet"
                />
              )}
              <Button onClick={submitClaim} disabled={status === "submitting" || (!walletPassword && !password)}>
                {status === "submitting" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                Claim 50% Refund
              </Button>
            </div>
          )}
          {status === "done" && <div className="flex items-center gap-2 text-emerald-400"><CheckCircle2 className="w-4 h-4" /> Refund submitted from your wallet.</div>}
        </div>
      </Card>
    </div>
  );
}
