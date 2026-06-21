"""
Portfolio constraint engine — mirrors the hard rules in the on-chain contract.
"""
from dataclasses import dataclass
from typing import Dict, List

ILLIQUID_CLASSES = {"defi_protocols", "tokenised_rwa", "alternatives", "real_estate"}
LIQUID_CLASSES   = {"stablecoins", "cash", "Cash", "fixed_income"}

# Asset class inference — maps common display names to canonical classes
INFERRED_CLASSES = {
    "equities": "equities", "equity": "equities", "stocks": "equities",
    "Equities": "equities", "Equity": "equities", "Stocks": "equities",
    "fixed income": "fixed_income", "fixed_income": "fixed_income",
    "bonds": "fixed_income", "bond": "fixed_income",
    "Fixed Income": "fixed_income", "Bonds": "fixed_income",
    "cash": "cash", "Cash": "cash",
    "stablecoins": "stablecoins", "Stablecoins": "stablecoins",
    "money market": "cash", "Money Market": "cash",
    "alternatives": "alternatives", "Alternatives": "alternatives",
    "real estate": "real_estate", "Real Estate": "real_estate",
    "reits": "real_estate", "REITs": "real_estate",
    "commodities": "commodities", "Commodities": "commodities",
    "crypto": "cryptocurrencies", "Crypto": "cryptocurrencies",
    "cryptocurrencies": "cryptocurrencies",
    "BTC": "cryptocurrencies", "ETH": "cryptocurrencies",
    "defi": "defi_protocols", "DeFi": "defi_protocols",
}


@dataclass
class ConstraintViolation:
    rule: str
    message: str
    current_value: float
    limit: float


def validate_portfolio_constraints(
    allocations: Dict[str, float],
    asset_classes: Dict[str, str],
) -> List[ConstraintViolation]:
    violations: List[ConstraintViolation] = []
    total = sum(allocations.values())

    # Infer missing asset classes from well-known display names
    resolved: Dict[str, str] = {}
    for asset_id in allocations:
        resolved[asset_id] = asset_classes.get(asset_id) or INFERRED_CLASSES.get(asset_id, "unknown")

    # Rule 1 — weights must sum to ~100%
    if abs(total - 100.0) > 0.5:
        violations.append(ConstraintViolation(
            rule="WEIGHT_SUM",
            message=f"Allocations must sum to 100% (got {total:.2f}%)",
            current_value=total, limit=100.0,
        ))

    # Rule 2 — max single asset concentration 70%
    for asset_id, weight in allocations.items():
        if weight > 70.0:
            violations.append(ConstraintViolation(
                rule="MAX_SINGLE_ASSET",
                message=f"Asset '{asset_id}' exceeds 70% max concentration ({weight:.2f}%)",
                current_value=weight, limit=70.0,
            ))

    # Rule 3 — max single asset class 80%
    class_totals: Dict[str, float] = {}
    for asset_id, weight in allocations.items():
        cls = resolved[asset_id]
        class_totals[cls] = class_totals.get(cls, 0.0) + weight
    for cls, total_weight in class_totals.items():
        if total_weight > 80.0:
            violations.append(ConstraintViolation(
                rule="MAX_ASSET_CLASS",
                message=f"Asset class '{cls}' exceeds 80% limit ({total_weight:.2f}%)",
                current_value=total_weight, limit=80.0,
            ))

    # Rule 4 — min liquidity reserve 2%
    liquid_weight = sum(class_totals.get(c, 0.0) for c in LIQUID_CLASSES)
    if liquid_weight < 2.0:
        violations.append(ConstraintViolation(
            rule="MIN_LIQUIDITY",
            message=f"Liquidity reserve below 2% minimum ({liquid_weight:.2f}%)",
            current_value=liquid_weight, limit=2.0,
        ))

    # Rule 5 — max illiquid allocation 40%
    illiquid_total = sum(class_totals.get(c, 0.0) for c in ILLIQUID_CLASSES)
    if illiquid_total > 40.0:
        violations.append(ConstraintViolation(
            rule="MAX_ILLIQUID",
            message=f"Illiquid allocation exceeds 40% ({illiquid_total:.2f}%)",
            current_value=illiquid_total, limit=40.0,
        ))

    # Rule 6 — min 2 asset classes
    active_classes = {resolved[a] for a in allocations if allocations.get(a, 0) > 0}
    if len(active_classes) < 2:
        violations.append(ConstraintViolation(
            rule="MIN_DIVERSIFICATION",
            message=f"Portfolio must span at least 2 asset classes (has {len(active_classes)})",
            current_value=float(len(active_classes)), limit=2.0,
        ))

    # Rule 7 — no leverage
    for asset_id, weight in allocations.items():
        if weight < 0:
            violations.append(ConstraintViolation(
                rule="NO_LEVERAGE",
                message=f"Asset '{asset_id}' has negative weight — leverage not permitted",
                current_value=weight, limit=0.0,
            ))

    # Rule 8 — max single DeFi protocol 15%
    for asset_id, weight in allocations.items():
        if resolved.get(asset_id) == "defi_protocols" and weight > 15.0:
            violations.append(ConstraintViolation(
                rule="MAX_DEFI_PROTOCOL",
                message=f"DeFi protocol '{asset_id}' exceeds 15% limit ({weight:.2f}%)",
                current_value=weight, limit=15.0,
            ))

    return violations
