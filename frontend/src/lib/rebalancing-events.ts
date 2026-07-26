"use client";

export const REBALANCING_UPDATED_EVENT = "allocensus:rebalancing-updated";

export function emitRebalancingUpdated(proposalId: string) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(REBALANCING_UPDATED_EVENT, { detail: { proposalId } }));
}
