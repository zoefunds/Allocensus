export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "portfolio_manager" | "analyst";
  is_active: boolean;
  is_email_verified: boolean;
  wallet_address: string | null;
  created_at: string;
}

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  total_value_usd: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  assets: PortfolioAsset[];
}

export interface PortfolioAsset {
  id: string;
  symbol: string;
  name: string;
  asset_class: string;
  quantity: number;
  current_price_usd: number;
  current_value_usd: number;
  target_weight_pct: number;
  current_weight_pct: number;
}

export interface Proposal {
  id: string;
  portfolio_id: string;
  status: "draft" | "submitted" | "pending_consensus" | "approved" | "rejected" | "failed";
  current_allocations: Record<string, number>;
  proposed_allocations: Record<string, number>;
  constraint_violations: ConstraintViolation[];
  genlayer_tx_hash: string | null;
  notes: string | null;
  created_at: string;
  rationale?: Rationale;
}

export interface ConstraintViolation {
  rule: string;
  message: string;
  current_value: number;
  limit: number;
}

export interface Rationale {
  id: string;
  proposal_id: string;
  approved: boolean;
  confidence_score: number | null;
  rationale_text: string;
  risk_analysis: string | null;
  constraint_analysis: string | null;
  diversification_score: number | null;
  liquidity_assessment: string | null;
  objective_alignment: string | null;
  validator_consensus: Record<string, unknown>;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  on_chain_ref: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}
