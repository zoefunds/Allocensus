"""
Portfolio constraint engine — 8 hard rules enforced before any rebalancing
submission reaches the Genlayer contract.
"""
from dataclasses import dataclass
from typing import Dict, List

ILLIQUID_CLASSES = {"defi_protocols", "tokenised_rwa"}


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
    """
    Validate allocation dict against hard portfolio rules.
    allocations: {asset_id: weight_pct}  (weights must sum to ~100)
    asset_classes: {asset_id: asset_class_name}
    Returns list of violations (empty = passes all constraints).
    """
    violations: List[ConstraintViolation] = []
    total = sum(allocations.values())

    # Rule 1 — weights must sum to ~100%
    if abs(total - 100.0) > 0.5:
        violations.append(ConstraintViolation(
            rule="WEIGHT_SUM",
            message=f"Allocations must sum to 100% (got {total:.2f}%)",
            current_value=total,
            limit=100.0,
        ))

    # Rule 2 — max single asset concentration 30%
    for asset_id, weight in allocations.items():
        if weight > 30.0:
            violations.append(ConstraintViolation(
                rule="MAX_SINGLE_ASSET",
                message=f"Asset '{asset_id}' exceeds 30% max concentration ({weight:.2f}%)",
                current_value=weight,
                limit=30.0,
            ))

    # Rule 3 — max single asset class 60%
    class_totals: Dict[str, float] = {}
    for asset_id, weight in allocations.items():
        cls = asset_classes.get(asset_id, "unknown")
        class_totals[cls] = class_totals.get(cls, 0.0) + weight
    for cls, total_weight in class_totals.items():
        if total_weight > 60.0:
            violations.append(ConstraintViolation(
                rule="MAX_ASSET_CLASS",
                message=f"Asset class '{cls}' exceeds 60% limit ({total_weight:.2f}%)",
                current_value=total_weight,
                limit=60.0,
            ))

    # Rule 4 — min liquidity reserve 5% (stablecoins / cash)
    liquid_weight = class_totals.get("stablecoins", 0.0) + class_totals.get("cash", 0.0)
    if liquid_weight < 5.0:
        violations.append(ConstraintViolation(
            rule="MIN_LIQUIDITY",
            message=f"Liquidity reserve below 5% minimum ({liquid_weight:.2f}%)",
            current_value=liquid_weight,
            limit=5.0,
        ))

    # Rule 5 — max illiquid allocation 25%
    illiquid_total = sum(class_totals.get(c, 0.0) for c in ILLIQUID_CLASSES)
    if illiquid_total > 25.0:
        violations.append(ConstraintViolation(
            rule="MAX_ILLIQUID",
            message=f"Illiquid allocation exceeds 25% ({illiquid_total:.2f}%)",
            current_value=illiquid_total,
            limit=25.0,
        ))

    # Rule 6 — min 3 asset classes
    active_classes = {cls for asset_id, cls in asset_classes.items() if allocations.get(asset_id, 0) > 0}
    if len(active_classes) < 3:
        violations.append(ConstraintViolation(
            rule="MIN_DIVERSIFICATION",
            message=f"Portfolio must span at least 3 asset classes (has {len(active_classes)})",
            current_value=float(len(active_classes)),
            limit=3.0,
        ))

    # Rule 7 — no leverage (negative weights)
    for asset_id, weight in allocations.items():
        if weight < 0:
            violations.append(ConstraintViolation(
                rule="NO_LEVERAGE",
                message=f"Asset '{asset_id}' has negative weight — leverage not permitted",
                current_value=weight,
                limit=0.0,
            ))

    # Rule 8 — max single DeFi protocol 15%
    for asset_id, weight in allocations.items():
        if asset_classes.get(asset_id) == "defi_protocols" and weight > 15.0:
            violations.append(ConstraintViolation(
                rule="MAX_DEFI_PROTOCOL",
                message=f"DeFi protocol '{asset_id}' exceeds 15% limit ({weight:.2f}%)",
                current_value=weight,
                limit=15.0,
            ))

    return violations
