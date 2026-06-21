"use client";

/**
 * useGenlayerTx — handles the full user-signed Genlayer transaction flow.
 *
 * Flow:
 *   1. GET /api/rebalancing/{id}/call-data  → backend returns call data + contract address
 *   2. User signs and broadcasts the tx via ethers.js using their wallet private key
 *      (decrypted client-side from localStorage — never sent to the server)
 *   3. POST /api/rebalancing/{id}/confirm-tx  with the tx_hash
 *   4. Poll /api/rebalancing/{id}/poll-result until consensus is reached
 *
 * The backend never receives or uses any private key.
 */

import { useState, useCallback } from "react";
import { ethers } from "ethers";
import { rebalancingAPI } from "@/lib/api";

export type TxStatus =
  | "idle"
  | "fetching_call_data"
  | "awaiting_signature"
  | "broadcasting"
  | "pending_consensus"
  | "confirmed"
  | "failed";

interface UseGenlayerTxResult {
  status:     TxStatus;
  txHash:     string | null;
  approved:   boolean | null;
  error:      string | null;
  submitProposal: (proposalId: string, privateKeyHex: string) => Promise<void>;
}

const GENLAYER_RPC = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "https://studio.genlayer.com/api";
const POLL_INTERVAL_MS = 6000;
const MAX_POLLS        = 40; // ~4 minutes max

export function useGenlayerTx(): UseGenlayerTxResult {
  const [status,   setStatus]   = useState<TxStatus>("idle");
  const [txHash,   setTxHash]   = useState<string | null>(null);
  const [approved, setApproved] = useState<boolean | null>(null);
  const [error,    setError]    = useState<string | null>(null);

  const submitProposal = useCallback(async (
    proposalId:    string,
    privateKeyHex: string,
  ) => {
    setStatus("fetching_call_data");
    setError(null);
    setTxHash(null);
    setApproved(null);

    try {
      // ── Step 1: Fetch call data from backend ────────────────────────────
      const callDataRes = await rebalancingAPI.getCallData(proposalId);
      const { call_data } = callDataRes.data;

      // ── Step 2: Sign and broadcast using the user's wallet ──────────────
      setStatus("awaiting_signature");

      const provider = new ethers.JsonRpcProvider(GENLAYER_RPC);
      const wallet   = new ethers.Wallet(privateKeyHex, provider);

      // Build the Genlayer transaction.
      // Genlayer uses a GenVM-specific encoding: method name + JSON args in data.
      const txData = JSON.stringify({
        method: call_data.method,
        args:   call_data.args,
      });

      const txRequest: ethers.TransactionRequest = {
        to:   call_data.to,
        data: ethers.hexlify(ethers.toUtf8Bytes(txData)),
      };

      setStatus("broadcasting");
      const txResponse = await wallet.sendTransaction(txRequest);
      const hash = txResponse.hash;
      setTxHash(hash);

      // ── Step 3: Record tx hash in backend ───────────────────────────────
      await rebalancingAPI.confirmTx(proposalId, hash);
      setStatus("pending_consensus");

      // ── Step 4: Poll backend until consensus is reached ─────────────────
      for (let i = 0; i < MAX_POLLS; i++) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
        try {
          const pollRes = await rebalancingAPI.pollResult(proposalId);
          const { status: pollStatus, approved: pollApproved } = pollRes.data;
          if (pollStatus !== "pending_consensus") {
            setApproved(pollApproved ?? null);
            setStatus("confirmed");
            return;
          }
        } catch {
          // transient error — keep polling
        }
      }

      // Timed out — status remains pending_consensus
      setError("Validators are still processing. Check back in a few minutes.");

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setStatus("failed");
    }
  }, []);

  return { status, txHash, approved, error, submitProposal };
}
