"use client";

/**
 * useGenlayerTx — handles the full user-signed Genlayer transaction flow.
 *
 * Genlayer architecture: transactions are NOT sent directly to the intelligent contract.
 * Instead, `addTransaction(sender, recipient, numValidators, maxRotations, data)` is called
 * on the Consensus Main Contract (0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575).
 * The `data` field is: RLP-serialize([genlayer_calldata, leaderOnly=false]).
 *
 * The backend never receives or uses any private key.
 */

import { useState, useCallback } from "react";
import { ethers } from "ethers";
import { abi as glAbi } from "genlayer-js";
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

const GENLAYER_RPC             = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || "https://studio.genlayer.com/api";
const CONSENSUS_MAIN_CONTRACT  = "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575";
const NUM_VALIDATORS           = BigInt(5);
const MAX_ROTATIONS            = BigInt(3);
const POLL_INTERVAL_MS         = 8000;
const MAX_POLLS                = 40;

// ABI for addTransaction on the Consensus Main Contract
const ADD_TRANSACTION_ABI = [
  {
    type: "function",
    name: "addTransaction",
    stateMutability: "nonpayable",
    inputs: [
      { name: "_sender",                  type: "address" },
      { name: "_recipient",               type: "address" },
      { name: "_numOfInitialValidators",  type: "uint256" },
      { name: "_maxRotations",            type: "uint256" },
      { name: "_txData",                  type: "bytes"   },
    ],
    outputs: [],
  },
] as const;

export function useGenlayerTx(): UseGenlayerTxResult {
  const [status,   setStatus]   = useState<TxStatus>("idle");
  const [txHash,   setTxHash]   = useState<string | null>(null);
  const [approved, setApproved] = useState<boolean | null>(null);
  const [error,    setError]    = useState<string | null>(null);

  const submitProposal = useCallback(async (proposalId: string, privateKeyHex: string) => {
    setStatus("fetching_call_data");
    setError(null);
    setTxHash(null);
    setApproved(null);

    try {
      // Step 1: fetch call data from backend
      const callDataRes = await rebalancingAPI.getCallData(proposalId);
      const { call_data } = callDataRes.data;

      // Step 2: encode calldata in Genlayer's binary format
      setStatus("awaiting_signature");

      const calldataObj = glAbi.calldata.makeCalldataObject(
        call_data.method,
        [],             // no positional args
        call_data.args, // keyword args
      );
      const encodedCalldata = glAbi.calldata.encode(calldataObj);

      // Genlayer tx data = RLP-serialize([calldata_bytes, leaderOnly_bool])
      const serializedData = glAbi.transactions.serialize([encodedCalldata, false]);

      // Step 3: ABI-encode the addTransaction call for the Consensus Main Contract
      const iface = new ethers.Interface(ADD_TRANSACTION_ABI);
      const provider = new ethers.JsonRpcProvider(GENLAYER_RPC);
      const wallet   = new ethers.Wallet(privateKeyHex, provider);

      const encodedCall = iface.encodeFunctionData("addTransaction", [
        wallet.address,           // _sender
        call_data.to,             // _recipient (the intelligent contract)
        NUM_VALIDATORS,
        MAX_ROTATIONS,
        serializedData,           // _txData
      ]);

      // Step 4: send to the Consensus Main Contract (gas-free on StudioNet)
      setStatus("broadcasting");
      const txResponse = await wallet.sendTransaction({
        to:       CONSENSUS_MAIN_CONTRACT,
        data:     encodedCall,
        gasPrice: BigInt(0),
        gasLimit: BigInt(1_000_000),
      });

      const hash = txResponse.hash;
      setTxHash(hash);

      // Step 5: record tx hash in backend
      await rebalancingAPI.confirmTx(proposalId, hash);
      setStatus("pending_consensus");

      // Step 6: poll until consensus
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
          // transient — keep polling
        }
      }

      setError("Validators are still processing. Check back in a few minutes.");

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setStatus("failed");
    }
  }, []);

  return { status, txHash, approved, error, submitProposal };
}
