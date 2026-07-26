from pydantic import BaseModel
from typing import Any, Dict, List


class InvestmentRulesResponse(BaseModel):
    version: str
    weight_sum: Dict[str, Any]
    single_asset_max_pct: float
    single_class_max_pct: float
    min_liquidity_pct: float
    max_illiquid_pct: float
    min_asset_classes: int
    no_leverage: bool
    max_defi_protocol_pct: float
    liquid_classes: List[str]
    illiquid_classes: List[str]
    supported_asset_classes: List[str]
