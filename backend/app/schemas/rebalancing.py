from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


class AllocationItem(BaseModel):
    symbol: str
    current_weight_pct: float
    proposed_weight_pct: float
    asset_class: str


class MarketContext(BaseModel):
    volatility_indicator: Optional[str] = None
    macro_signals: Optional[str] = None
    market_regime: Optional[str] = None
    additional_context: Optional[str] = None


class ProposalCreate(BaseModel):
    portfolio_id: uuid.UUID
    proposed_allocations: Dict[str, float]
    market_context: MarketContext = MarketContext()
    notes: Optional[str] = None


class ConstraintViolationOut(BaseModel):
    rule: str
    message: str
    current_value: float
    limit: float


class ProposalResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    status: str
    current_allocations: Dict[str, Any]
    proposed_allocations: Dict[str, Any]
    constraint_violations: List[ConstraintViolationOut]
    genlayer_tx_hash: Optional[str]
    notes: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class RationaleResponse(BaseModel):
    id: uuid.UUID
    proposal_id: uuid.UUID
    approved: bool
    confidence_score: Optional[float]
    rationale_text: str
    risk_analysis: Optional[str]
    constraint_analysis: Optional[str]
    diversification_score: Optional[float]
    liquidity_assessment: Optional[str]
    objective_alignment: Optional[str]
    validator_consensus: Dict[str, Any]
    created_at: datetime
    model_config = {"from_attributes": True}
