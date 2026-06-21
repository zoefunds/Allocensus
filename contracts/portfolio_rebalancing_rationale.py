# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# =============================================================================
# ALLOCENSUS — Portfolio Rebalancing Rationale Contract
# Network  : Genlayer StudioNet
# Token    : GEN
# Version  : 1.0.0
#
# Purpose  : Evaluate proposed portfolio rebalancing decisions using LLM-powered
#            reasoning and Genlayer validator consensus. Each evaluation produces
#            a transparent, auditable rationale stored permanently on-chain.
#
# Consensus: Uses gl.eq_principle.prompt_comparative with a principle that only
#            requires validators to agree on the binary approved/rejected decision.
#            Reasoning text may differ between validators — this prevents
#            undetermined status while preserving intellectual diversity.
# =============================================================================

from genlayer import *

import json


# ─── CONSTRAINT CONSTANTS ────────────────────────────────────────────────────

MAX_SINGLE_ASSET_PCT     = 70.0   # single position cap (generous for broad asset classes)
MAX_SINGLE_CLASS_PCT     = 80.0   # single asset-class cap
MIN_LIQUIDITY_PCT        = 2.0    # minimum cash/stablecoin reserve
MAX_ILLIQUID_PCT         = 40.0   # max illiquid exposure
MIN_ASSET_CLASSES        = 2      # minimum distinct asset classes
MAX_DEFI_PROTOCOL_PCT    = 15.0
MAX_LEVERAGE             = 0.0

ILLIQUID_CLASSES = {"defi_protocols", "tokenised_rwa", "alternatives", "real_estate"}
LIQUID_CLASSES   = {"stablecoins", "cash", "Cash", "fixed_income"}

# ─── ASSET CLASS INFERENCE MAP ───────────────────────────────────────────────
# Maps common display names → canonical class. Applied when caller passes empty
# asset_classes dict (e.g. proposals created with broad allocation labels).
INFERRED_CLASSES = {
    # Equities
    "equities": "equities", "equity": "equities", "stocks": "equities",
    "Equities": "equities", "Equity": "equities", "Stocks": "equities",
    # Fixed income
    "fixed income": "fixed_income", "fixed_income": "fixed_income",
    "bonds": "fixed_income", "bond": "fixed_income",
    "Fixed Income": "fixed_income", "Bonds": "fixed_income",
    # Cash / stablecoins
    "cash": "cash", "Cash": "cash",
    "stablecoins": "stablecoins", "Stablecoins": "stablecoins",
    "money market": "cash", "Money Market": "cash",
    # Alternatives
    "alternatives": "alternatives", "Alternatives": "alternatives",
    "alternative": "alternatives", "Alternative": "alternatives",
    # Real estate
    "real estate": "real_estate", "Real Estate": "real_estate",
    "reits": "real_estate", "REITs": "real_estate",
    # Commodities
    "commodities": "commodities", "Commodities": "commodities",
    "commodity": "commodities", "Commodity": "commodities",
    # Crypto
    "crypto": "cryptocurrencies", "Crypto": "cryptocurrencies",
    "cryptocurrencies": "cryptocurrencies", "bitcoin": "cryptocurrencies",
    "BTC": "cryptocurrencies", "ETH": "cryptocurrencies",
    # DeFi
    "defi": "defi_protocols", "DeFi": "defi_protocols",
}

RISK_PROFILES = {
    "conservative":    {"max_crypto_pct": 20.0,  "max_equity_pct": 40.0, "min_fixed_income_pct": 20.0},
    "moderate":        {"max_crypto_pct": 35.0,  "max_equity_pct": 60.0, "min_fixed_income_pct": 10.0},
    "aggressive":      {"max_crypto_pct": 60.0,  "max_equity_pct": 80.0, "min_fixed_income_pct": 0.0},
    "very_aggressive": {"max_crypto_pct": 90.0,  "max_equity_pct": 90.0, "min_fixed_income_pct": 0.0},
}

HORIZON_LABELS = {
    "short":     "less than 1 year",
    "medium":    "1 to 5 years",
    "long":      "5 to 10 years",
    "very_long": "more than 10 years",
}


# ─── CONTRACT ────────────────────────────────────────────────────────────────

class PortfolioRebalancingRationale(gl.Contract):
    """
    Allocensus Portfolio Rebalancing Rationale Contract.

    Stores all evaluated proposals on-chain. Each proposal record contains
    the full AI rationale, constraint analysis, risk assessment, and the
    final approved/rejected decision reached by validator consensus.

    State variables (persistent on-chain):
      proposals_json   : JSON-encoded map of proposal_id -> evaluation result
      proposal_ids     : ordered list of all proposal IDs ever submitted
      total_evaluated  : running count of evaluations
      total_approved   : running count of approved evaluations
      total_rejected   : running count of rejected evaluations
      owner_address    : the deployer address (admin)
      contract_version : semantic version string
    """

    proposals_json:   TreeMap[str, str]
    proposal_ids:     DynArray[str]
    total_evaluated:  u256
    total_approved:   u256
    total_rejected:   u256
    owner_address:    Address
    contract_version: str

    def __init__(self) -> None:
        # TreeMap and DynArray are initialized automatically by the Genlayer
        # runtime from the type annotations above — do NOT instantiate them here.
        self.total_evaluated  = u256(0)
        self.total_approved   = u256(0)
        self.total_rejected   = u256(0)
        self.owner_address    = gl.message.sender_address
        self.contract_version = "1.0.0"


    # =========================================================================
    # PUBLIC VIEW METHODS
    # =========================================================================

    @gl.public.view
    def get_proposal(self, proposal_id: str) -> str:
        return self.proposals_json.get(proposal_id, "{}")

    @gl.public.view
    def get_proposal_ids(self) -> list[str]:
        return list(self.proposal_ids)

    @gl.public.view
    def get_stats(self) -> str:
        total    = int(self.total_evaluated)
        approved = int(self.total_approved)
        rejected = int(self.total_rejected)
        rate     = round((approved / total * 100), 2) if total > 0 else 0.0
        return json.dumps({
            "total_evaluated":   total,
            "total_approved":    approved,
            "total_rejected":    rejected,
            "approval_rate_pct": rate,
            "contract_version":  self.contract_version,
            "owner":             str(self.owner_address),
        })

    @gl.public.view
    def get_owner(self) -> str:
        return str(self.owner_address)

    @gl.public.view
    def get_version(self) -> str:
        return self.contract_version

    @gl.public.view
    def proposal_exists(self, proposal_id: str) -> bool:
        return proposal_id in self.proposals_json

    @gl.public.view
    def get_decision(self, proposal_id: str) -> str:
        raw = self.proposals_json.get(proposal_id, "")
        if not raw:
            return "not_found"
        try:
            data = json.loads(raw)
            return "approved" if data.get("approved", False) else "rejected"
        except Exception:
            return "not_found"

    @gl.public.view
    def get_recent_proposals(self, count: int) -> str:
        cap     = min(count, 50)
        all_ids = list(self.proposal_ids)
        recent  = all_ids[-cap:] if len(all_ids) >= cap else all_ids
        results = []
        for pid in reversed(recent):
            decision = self.get_decision(pid)
            results.append({"proposal_id": pid, "decision": decision})
        return json.dumps(results)

    @gl.public.view
    def get_constraint_rules(self) -> str:
        return json.dumps({
            "rules": [
                {
                    "id": "WEIGHT_SUM",
                    "description": "All asset weights must sum to 100% (±0.5%)",
                    "limit": 100.0,
                    "hard": True,
                },
                {
                    "id": "MAX_SINGLE_ASSET",
                    "description": "No single asset may exceed 30% of the portfolio",
                    "limit": MAX_SINGLE_ASSET_PCT,
                    "hard": True,
                },
                {
                    "id": "MAX_ASSET_CLASS",
                    "description": "No single asset class may exceed 60% of the portfolio",
                    "limit": MAX_SINGLE_CLASS_PCT,
                    "hard": True,
                },
                {
                    "id": "MIN_LIQUIDITY",
                    "description": "Stablecoins and cash must represent at least 5% of the portfolio",
                    "limit": MIN_LIQUIDITY_PCT,
                    "hard": True,
                },
                {
                    "id": "MAX_ILLIQUID",
                    "description": "DeFi protocols and illiquid RWA combined may not exceed 25%",
                    "limit": MAX_ILLIQUID_PCT,
                    "hard": True,
                },
                {
                    "id": "MIN_DIVERSIFICATION",
                    "description": "Portfolio must span at least 3 distinct asset classes",
                    "limit": float(MIN_ASSET_CLASSES),
                    "hard": True,
                },
                {
                    "id": "NO_LEVERAGE",
                    "description": "All asset weights must be non-negative (no short positions)",
                    "limit": 0.0,
                    "hard": True,
                },
                {
                    "id": "MAX_DEFI_PROTOCOL",
                    "description": "No single DeFi protocol may exceed 15% of the portfolio",
                    "limit": MAX_DEFI_PROTOCOL_PCT,
                    "hard": True,
                },
            ],
            "supported_asset_classes": [
                "cryptocurrencies",
                "tokenised_rwa",
                "defi_protocols",
                "equities",
                "fixed_income",
                "commodities",
                "stablecoins",
                "cash",
            ],
            "supported_risk_profiles": list(RISK_PROFILES.keys()),
            "supported_horizons": list(HORIZON_LABELS.keys()),
        })


    # =========================================================================
    # PUBLIC WRITE METHODS
    # =========================================================================

    @gl.public.write
    def evaluate_rebalancing(
        self,
        proposal_id:        str,
        current_portfolio:  str,
        proposed_portfolio: str,
        asset_classes:      str,
        investor_profile:   str,
        market_context:     str,
    ) -> None:
        """
        Evaluate a portfolio rebalancing proposal using Genlayer LLM consensus.

        Parameters:
          proposal_id        — unique identifier for this proposal
          current_portfolio  — JSON: {"BTC": 25.0, "ETH": 15.0, ...}
          proposed_portfolio — JSON: {"BTC": 20.0, "ETH": 20.0, ...}
          asset_classes      — JSON: {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", ...}
          investor_profile   — JSON: {"risk_tolerance": "moderate", "investment_horizon": "long",
                                      "investment_objectives": ["capital growth"],
                                      "liquidity_requirements": "standard"}
          market_context     — JSON: {"volatility_indicator": "medium",
                                      "macro_signals": "neutral",
                                      "market_regime": "bull",
                                      "additional_context": ""}

        Consensus strategy: prompt_comparative requires validators to agree only on
        the binary `approved` field. Reasoning text may legitimately differ.
        """

        # ── Guard: prevent duplicate evaluation ───────────────────────────────
        if proposal_id in self.proposals_json:
            raise gl.vm.UserError(
                f"[EXPECTED] Proposal '{proposal_id}' has already been evaluated."
            )

        # ── Parse inputs ──────────────────────────────────────────────────────
        try:
            current  = json.loads(current_portfolio)
            proposed = json.loads(proposed_portfolio)
            classes  = json.loads(asset_classes)
            profile  = json.loads(investor_profile)
            context  = json.loads(market_context)
        except json.JSONDecodeError as e:
            raise gl.vm.UserError(f"[EXPECTED] Invalid JSON input: {e}")

        if not proposed:
            raise gl.vm.UserError("[EXPECTED] Proposed portfolio is empty.")
        if not current:
            raise gl.vm.UserError("[EXPECTED] Current portfolio is empty.")

        # ── Infer missing asset classes from well-known display names ─────────
        if not classes:
            classes = {}
        all_symbols = set(list(current.keys()) + list(proposed.keys()))
        for sym in all_symbols:
            if sym not in classes:
                classes[sym] = INFERRED_CLASSES.get(sym, "unknown")

        # ── Deterministic constraint pre-check ────────────────────────────────
        constraint_result  = self._check_all_constraints(proposed, classes)
        hard_fail          = constraint_result["hard_fail"]
        violations         = constraint_result["violations"]
        constraint_summary = constraint_result["summary"]

        # ── Deterministic portfolio analytics ─────────────────────────────────
        analytics = self._compute_analytics(current, proposed, classes)

        # ── Precompute all prompt strings (deterministic, before nondet block) ─
        risk_tolerance     = profile.get("risk_tolerance", "moderate")
        investment_horizon = profile.get("investment_horizon", "long")
        objectives_list    = profile.get("investment_objectives", ["capital growth"])
        liquidity_req      = profile.get("liquidity_requirements", "standard")
        objectives_str     = ", ".join(objectives_list) if objectives_list else "capital growth"
        horizon_label      = HORIZON_LABELS.get(investment_horizon, investment_horizon)
        risk_profile_rules = self._get_risk_profile_rules(risk_tolerance)

        current_str         = self._format_allocations(current)
        proposed_str        = self._format_allocations(proposed)
        drift_str           = self._format_drift(analytics["drift"])
        class_summary_str   = self._format_class_summary(analytics["class_totals"])
        diversification_str = self._format_diversification(analytics)
        liquidity_str       = self._format_liquidity(analytics)
        volatility_signal   = context.get("volatility_indicator", "not specified")
        macro_signal        = context.get("macro_signals", "not specified")
        market_regime       = context.get("market_regime", "not specified")
        extra_context       = context.get("additional_context", "")
        violations_text     = (
            "\n".join(f"  - [{v['rule']}] {v['message']}" for v in violations)
            if violations else "  None"
        )
        hard_fail_str       = "YES — AUTOMATIC REJECTION" if hard_fail else "No"

        # ── Non-deterministic LLM evaluation ─────────────────────────────────
        # Both leader and each validator independently execute get_evaluation().
        # The eq_principle compares ONLY the `approved` boolean.
        # Reasoning paragraphs, scores, and analyses may vary between validators.
        # This design ensures consensus is reachable on subjective analyses.

        def get_evaluation() -> str:
            market_intel = ""
            try:
                fear_greed_raw = gl.nondet.web.get(
                    "https://api.alternative.me/fng/?limit=1&format=json",
                    mode="text",
                )
                market_intel += f"Fear & Greed Index: {str(fear_greed_raw)[:250]}\n"
            except Exception:
                market_intel += "Fear & Greed Index: data unavailable\n"

            try:
                global_raw = gl.nondet.web.get(
                    "https://api.coingecko.com/api/v3/global",
                    mode="text",
                )
                market_intel += f"Crypto Market Cap Data: {str(global_raw)[:350]}\n"
            except Exception:
                market_intel += "Crypto Market Cap Data: unavailable\n"

            prompt = f"""You are a senior portfolio risk analyst at an institutional asset management firm specializing in multi-asset portfolios including crypto, tokenised real-world assets, DeFi protocols, equities, fixed income, and commodities.

Your task is to evaluate a proposed portfolio rebalancing decision and produce a structured JSON assessment.

=== INVESTOR PROFILE ===
Risk Tolerance        : {risk_tolerance}
Investment Horizon    : {horizon_label}
Investment Objectives : {objectives_str}
Liquidity Requirements: {liquidity_req}
Risk Profile Rules    : {risk_profile_rules}

=== CURRENT PORTFOLIO ===
{current_str}

=== PROPOSED PORTFOLIO ===
{proposed_str}

=== ALLOCATION CHANGES (drift) ===
{drift_str}

=== ASSET CLASS BREAKDOWN ===
{class_summary_str}

=== PORTFOLIO ANALYTICS ===
{diversification_str}
{liquidity_str}

=== CONSTRAINT PRE-CHECK RESULTS (deterministic — these are facts) ===
Hard Constraint Fail : {hard_fail_str}
Violations Found     : {len(violations)}
{violations_text}

Full constraint report:
{constraint_summary}

=== MARKET CONTEXT (provided by portfolio manager) ===
Volatility Indicator : {volatility_signal}
Macro Signals        : {macro_signal}
Market Regime        : {market_regime}
Additional Context   : {extra_context if extra_context else "None"}

=== LIVE MARKET INTELLIGENCE (fetched at evaluation time) ===
{market_intel}

=== EVALUATION DIMENSIONS ===

You must evaluate this rebalancing proposal across 6 dimensions:

1. CONSTRAINT COMPLIANCE
   - If "Hard Constraint Fail" is YES above, you MUST set approved to false — this is non-negotiable.
   - Borderline cases (close to a limit but not over) should be noted and may factor into confidence.
   - If all constraints pass, constraints do not contribute negatively to the decision.

2. RISK ALIGNMENT
   - Does the proposed portfolio match the investor's risk tolerance ({risk_tolerance})?
   - Does the portfolio follow the risk profile rules: {risk_profile_rules}?
   - Does the investment horizon ({horizon_label}) justify the proposed changes?
   - Significant misalignment between proposed risk level and investor profile should lead to rejection.
   - Minor deviations from optimal risk positioning with valid reasoning may still be approved.

3. DIVERSIFICATION QUALITY
   - Score from 0 to 100. 0 = single asset, 100 = perfectly equal spread.
   - Consider number of asset classes, concentration in any single position, correlation between assets.
   - Does the rebalance improve or worsen cross-asset diversification?

4. LIQUIDITY ADEQUACY
   - Does the post-rebalance portfolio maintain adequate liquid assets for the investor's needs?
   - Current liquid reserve: {analytics['liquid_pct']:.2f}% (stablecoins + cash)
   - Minimum required: {MIN_LIQUIDITY_PCT}%
   - Is liquidity sufficient for the stated liquidity requirements?

5. INVESTMENT OBJECTIVE ALIGNMENT
   - Do the proposed changes serve the stated objectives: {objectives_str}?
   - Is the direction of change (increasing/decreasing each position) aligned with these goals?
   - Growth objectives favor higher risk/return assets; preservation objectives favor stability.

6. MARKET CONTEXT APPROPRIATENESS
   - Given the market conditions provided and the live market data, is this rebalancing timely?
   - Does the macro environment support or contradict the proposed changes?
   - Are there clear market signals that make this a particularly good or bad time to rebalance?

=== APPROVAL GUIDANCE ===
APPROVE when:
  - All hard constraints pass (no violations)
  - Risk level is broadly appropriate for the investor's profile
  - The rebalancing direction is constructive for the investor's stated objectives
  - Market context is neutral to supportive
  - Liquidity requirements are met

REJECT when:
  - ANY hard constraint is violated (automatic rejection)
  - Risk level is fundamentally misaligned with the investor profile (e.g. 80% crypto for a conservative investor)
  - The proposed changes would clearly harm the investor's stated objectives
  - Market context strongly argues against the rebalancing at this time

IMPORTANT: Be appropriately balanced in your judgment. Do not reject well-constructed proposals
that pass constraints and are directionally sound for the investor's goals. Minor imperfections
in an otherwise sound proposal should not trigger rejection. Reject only when there is a clear,
defensible reason.

=== REQUIRED OUTPUT FORMAT ===
Respond ONLY with valid JSON. No markdown code fences. No text before or after the JSON object.
The JSON must be parseable by a standard JSON parser without any modifications.

{{
  "approved": true,
  "confidence_score": 0.82,
  "overall_rationale": "2-4 paragraph institutional analysis explaining the decision",
  "constraint_analysis": "Assessment of all 8 hard constraints: which pass, fail, or are borderline",
  "risk_analysis": "How this rebalance changes the risk profile relative to the investor's tolerance",
  "diversification_score": 72,
  "diversification_analysis": "Assessment of diversification quality and changes",
  "liquidity_assessment": "Assessment of liquidity adequacy post-rebalance",
  "objective_alignment": "How well this rebalance serves the stated investment objectives",
  "market_context_analysis": "Assessment of timing given market conditions and live data",
  "key_risks_introduced": ["List of specific risks this rebalance introduces"],
  "key_risks_mitigated": ["List of specific risks this rebalance reduces or eliminates"],
  "recommendation": "Single clear actionable sentence summarizing what should happen next"
}}

Replace the example values with your actual analysis. The "approved" field must be true or false (boolean). The "confidence_score" must be a decimal between 0.5 and 1.0. The "diversification_score" must be an integer between 0 and 100."""

            raw = gl.nondet.exec_prompt(prompt)
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            return cleaned

        # ── Run consensus evaluation ──────────────────────────────────────────
        raw_result = gl.eq_principle.prompt_comparative(
            get_evaluation,
            'The "approved" field must match exactly (both true or both false). '
            'Confidence scores, reasoning text, scores, and all other fields may '
            'reasonably differ between validators and do not need to match.'
        )

        # ── Parse result ──────────────────────────────────────────────────────
        try:
            evaluation = json.loads(raw_result)
        except json.JSONDecodeError:
            start = raw_result.find("{")
            end   = raw_result.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    evaluation = json.loads(raw_result[start:end])
                except json.JSONDecodeError:
                    evaluation = self._build_fallback_result(
                        hard_fail, violations, constraint_summary, raw_result
                    )
            else:
                evaluation = self._build_fallback_result(
                    hard_fail, violations, constraint_summary, raw_result
                )

        # ── Enforce hard constraint rejection (deterministic override) ────────
        if hard_fail:
            evaluation["approved"] = False
            evaluation["hard_constraint_fail"] = True
            violation_msgs = "; ".join(v["message"] for v in violations)
            existing_rationale = evaluation.get("overall_rationale", "")
            evaluation["overall_rationale"] = (
                f"AUTOMATICALLY REJECTED due to {len(violations)} hard constraint violation(s): "
                f"{violation_msgs}. Hard constraints represent non-negotiable institutional "
                f"risk management rules and cannot be overridden by any AI evaluation. "
                f"Additional analysis: {existing_rationale}"
            )

        approved = bool(evaluation.get("approved", False))

        # ── Build final on-chain record ───────────────────────────────────────
        final_record = {
            "proposal_id":              proposal_id,
            "approved":                 approved,
            "submitted_by":             str(gl.message.sender_address),
            "confidence_score":         evaluation.get("confidence_score", 0.7),
            "overall_rationale":        evaluation.get("overall_rationale", ""),
            "constraint_analysis":      evaluation.get("constraint_analysis", ""),
            "risk_analysis":            evaluation.get("risk_analysis", ""),
            "diversification_score":    evaluation.get("diversification_score", 50),
            "diversification_analysis": evaluation.get("diversification_analysis", ""),
            "liquidity_assessment":     evaluation.get("liquidity_assessment", ""),
            "objective_alignment":      evaluation.get("objective_alignment", ""),
            "market_context_analysis":  evaluation.get("market_context_analysis", ""),
            "key_risks_introduced":     evaluation.get("key_risks_introduced", []),
            "key_risks_mitigated":      evaluation.get("key_risks_mitigated", []),
            "recommendation":           evaluation.get("recommendation", ""),
            "hard_constraint_fail":     hard_fail,
            "violations_count":         len(violations),
            "violations":               violations,
            "constraint_summary":       constraint_summary,
            "analytics": {
                "class_totals":            analytics["class_totals"],
                "liquid_pct":              analytics["liquid_pct"],
                "illiquid_pct":            analytics["illiquid_pct"],
                "asset_count":             analytics["asset_count"],
                "class_count":             analytics["class_count"],
                "max_single_asset_pct":    analytics["max_single_asset_pct"],
                "max_single_asset_symbol": analytics["max_single_asset_symbol"],
                "total_drift":             analytics["total_drift"],
                "hhi":                     analytics["hhi"],
            },
            "inputs": {
                "current_portfolio":  current,
                "proposed_portfolio": proposed,
                "asset_classes":      classes,
                "investor_profile":   profile,
                "market_context":     context,
            },
        }

        # ── Persist on-chain ──────────────────────────────────────────────────
        self.proposals_json[proposal_id] = json.dumps(final_record)
        self.proposal_ids.append(proposal_id)

        self.total_evaluated = self.total_evaluated + u256(1)
        if approved:
            self.total_approved = self.total_approved + u256(1)
        else:
            self.total_rejected = self.total_rejected + u256(1)


    @gl.public.write
    def delete_proposal(self, proposal_id: str) -> None:
        if gl.message.sender_address != self.owner_address:
            raise gl.vm.UserError("[EXPECTED] Only the contract owner can delete proposals.")
        if proposal_id not in self.proposals_json:
            raise gl.vm.UserError(f"[EXPECTED] Proposal '{proposal_id}' not found.")
        del self.proposals_json[proposal_id]


    # =========================================================================
    # PRIVATE DETERMINISTIC HELPERS
    # =========================================================================

    def _check_all_constraints(self, proposed: dict, asset_classes: dict) -> dict:
        violations = []
        lines      = []

        # Rule 1: Weight sum
        total = sum(float(v) for v in proposed.values())
        if abs(total - 100.0) > 0.5:
            violations.append({
                "rule":    "WEIGHT_SUM",
                "message": f"Allocations sum to {total:.2f}% — must be 100% ±0.5%",
                "value":   round(total, 2),
                "limit":   100.0,
            })
            lines.append(f"[FAIL] WEIGHT_SUM: {total:.2f}%")
        else:
            lines.append(f"[PASS] WEIGHT_SUM: {total:.2f}%")

        # Rule 2: Max single asset
        for symbol, raw_weight in proposed.items():
            weight = float(raw_weight)
            if weight > MAX_SINGLE_ASSET_PCT:
                violations.append({
                    "rule":    "MAX_SINGLE_ASSET",
                    "message": f"{symbol} = {weight:.2f}% (max {MAX_SINGLE_ASSET_PCT}%)",
                    "value":   round(weight, 2),
                    "limit":   MAX_SINGLE_ASSET_PCT,
                    "symbol":  symbol,
                })
                lines.append(f"[FAIL] MAX_SINGLE_ASSET: {symbol} = {weight:.2f}%")
            else:
                lines.append(f"[PASS] MAX_SINGLE_ASSET: {symbol} = {weight:.2f}%")

        # Rule 3: Max asset class
        class_totals = self._compute_class_totals(proposed, asset_classes)
        for cls, cls_total in class_totals.items():
            if cls_total > MAX_SINGLE_CLASS_PCT:
                violations.append({
                    "rule":    "MAX_ASSET_CLASS",
                    "message": f"Class '{cls}' = {cls_total:.2f}% (max {MAX_SINGLE_CLASS_PCT}%)",
                    "value":   round(cls_total, 2),
                    "limit":   MAX_SINGLE_CLASS_PCT,
                    "class":   cls,
                })
                lines.append(f"[FAIL] MAX_ASSET_CLASS: {cls} = {cls_total:.2f}%")
            else:
                lines.append(f"[PASS] MAX_ASSET_CLASS: {cls} = {cls_total:.2f}%")

        # Rule 4: Min liquidity
        liquid_pct = sum(class_totals.get(c, 0.0) for c in LIQUID_CLASSES)
        if liquid_pct < MIN_LIQUIDITY_PCT:
            violations.append({
                "rule":    "MIN_LIQUIDITY",
                "message": f"Liquid reserve = {liquid_pct:.2f}% (minimum {MIN_LIQUIDITY_PCT}%)",
                "value":   round(liquid_pct, 2),
                "limit":   MIN_LIQUIDITY_PCT,
            })
            lines.append(f"[FAIL] MIN_LIQUIDITY: {liquid_pct:.2f}%")
        else:
            lines.append(f"[PASS] MIN_LIQUIDITY: {liquid_pct:.2f}%")

        # Rule 5: Max illiquid
        illiquid_pct = sum(class_totals.get(c, 0.0) for c in ILLIQUID_CLASSES)
        if illiquid_pct > MAX_ILLIQUID_PCT:
            violations.append({
                "rule":    "MAX_ILLIQUID",
                "message": f"Illiquid total = {illiquid_pct:.2f}% (max {MAX_ILLIQUID_PCT}%)",
                "value":   round(illiquid_pct, 2),
                "limit":   MAX_ILLIQUID_PCT,
            })
            lines.append(f"[FAIL] MAX_ILLIQUID: {illiquid_pct:.2f}%")
        else:
            lines.append(f"[PASS] MAX_ILLIQUID: {illiquid_pct:.2f}%")

        # Rule 6: Min 3 asset classes
        active_classes = set()
        for symbol, raw_weight in proposed.items():
            if float(raw_weight) > 0:
                active_classes.add(asset_classes.get(symbol, "unknown"))
        class_count = len(active_classes)
        if class_count < MIN_ASSET_CLASSES:
            violations.append({
                "rule":    "MIN_DIVERSIFICATION",
                "message": f"Only {class_count} asset class(es) — minimum is {MIN_ASSET_CLASSES}",
                "value":   float(class_count),
                "limit":   float(MIN_ASSET_CLASSES),
            })
            lines.append(f"[FAIL] MIN_DIVERSIFICATION: {class_count} classes")
        else:
            lines.append(f"[PASS] MIN_DIVERSIFICATION: {class_count} classes")

        # Rule 7: No leverage
        for symbol, raw_weight in proposed.items():
            weight = float(raw_weight)
            if weight < MAX_LEVERAGE:
                violations.append({
                    "rule":    "NO_LEVERAGE",
                    "message": f"{symbol} = {weight:.2f}% — no negative weights permitted",
                    "value":   round(weight, 2),
                    "limit":   0.0,
                    "symbol":  symbol,
                })
                lines.append(f"[FAIL] NO_LEVERAGE: {symbol} = {weight:.2f}%")

        # Rule 8: Max DeFi protocol
        for symbol, raw_weight in proposed.items():
            weight = float(raw_weight)
            if asset_classes.get(symbol, "") == "defi_protocols" and weight > MAX_DEFI_PROTOCOL_PCT:
                violations.append({
                    "rule":    "MAX_DEFI_PROTOCOL",
                    "message": f"DeFi protocol {symbol} = {weight:.2f}% (max {MAX_DEFI_PROTOCOL_PCT}%)",
                    "value":   round(weight, 2),
                    "limit":   MAX_DEFI_PROTOCOL_PCT,
                    "symbol":  symbol,
                })
                lines.append(f"[FAIL] MAX_DEFI_PROTOCOL: {symbol} = {weight:.2f}%")

        return {
            "hard_fail":  len(violations) > 0,
            "violations": violations,
            "summary":    "\n".join(lines),
        }


    def _compute_class_totals(self, allocations: dict, asset_classes: dict) -> dict:
        totals: dict = {}
        for symbol, raw_weight in allocations.items():
            cls = asset_classes.get(symbol, "unknown")
            totals[cls] = totals.get(cls, 0.0) + float(raw_weight)
        return totals


    def _compute_analytics(self, current: dict, proposed: dict, asset_classes: dict) -> dict:
        class_totals = self._compute_class_totals(proposed, asset_classes)

        liquid_pct   = sum(class_totals.get(c, 0.0) for c in LIQUID_CLASSES)
        illiquid_pct = sum(class_totals.get(c, 0.0) for c in ILLIQUID_CLASSES)

        active_classes = set()
        for symbol, raw_weight in proposed.items():
            if float(raw_weight) > 0:
                active_classes.add(asset_classes.get(symbol, "unknown"))

        max_weight = 0.0
        max_symbol = ""
        for symbol, raw_weight in proposed.items():
            w = float(raw_weight)
            if w > max_weight:
                max_weight = w
                max_symbol = symbol

        all_symbols = set(list(current.keys()) + list(proposed.keys()))
        drift_map   = {}
        total_drift = 0.0
        for s in all_symbols:
            cur_w  = float(current.get(s, 0.0))
            prop_w = float(proposed.get(s, 0.0))
            delta  = prop_w - cur_w
            if abs(delta) >= 0.01:
                drift_map[s] = round(delta, 2)
            total_drift += abs(delta)

        hhi = sum((float(w) / 100.0) ** 2 for w in proposed.values())
        n   = max(len(proposed), 1)
        min_hhi = 1.0 / n
        raw_div = 100.0 * (1.0 - (hhi - min_hhi) / max(1.0 - min_hhi, 0.001))
        div_score = max(0, min(100, round(raw_div, 1)))

        return {
            "class_totals":            {k: round(v, 2) for k, v in class_totals.items()},
            "liquid_pct":              round(liquid_pct, 2),
            "illiquid_pct":            round(illiquid_pct, 2),
            "asset_count":             len(proposed),
            "class_count":             len(active_classes),
            "active_classes":          sorted(list(active_classes)),
            "max_single_asset_pct":    round(max_weight, 2),
            "max_single_asset_symbol": max_symbol,
            "total_drift":             round(total_drift, 2),
            "drift":                   drift_map,
            "hhi":                     round(hhi, 4),
            "diversification_score":   div_score,
        }


    def _get_risk_profile_rules(self, risk_tolerance: str) -> str:
        rules = RISK_PROFILES.get(risk_tolerance, RISK_PROFILES["moderate"])
        return (
            f"max crypto {rules['max_crypto_pct']}%, "
            f"max equity {rules['max_equity_pct']}%, "
            f"min fixed income {rules['min_fixed_income_pct']}%"
        )


    def _format_allocations(self, allocations: dict) -> str:
        lines = []
        sorted_items = sorted(allocations.items(), key=lambda x: float(x[1]), reverse=True)
        for symbol, weight in sorted_items:
            bar = "#" * int(float(weight) / 2)
            lines.append(f"  {symbol:<14} {float(weight):>6.2f}%  {bar}")
        return "\n".join(lines) if lines else "  (empty)"


    def _format_drift(self, drift_map: dict) -> str:
        if not drift_map:
            return "  No material allocation changes."
        lines = []
        for symbol, delta in sorted(drift_map.items(), key=lambda x: abs(x[1]), reverse=True):
            direction = "+" if delta > 0 else ""
            lines.append(f"  {symbol:<14} {direction}{delta:>+.2f}%")
        return "\n".join(lines)


    def _format_class_summary(self, class_totals: dict) -> str:
        lines = []
        for cls, total in sorted(class_totals.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cls:<25} {total:>6.2f}%")
        return "\n".join(lines) if lines else "  No class data"


    def _format_diversification(self, analytics: dict) -> str:
        return (
            f"  Assets: {analytics['asset_count']}  |  "
            f"Classes: {analytics['class_count']} ({', '.join(analytics.get('active_classes', []))})\n"
            f"  HHI: {analytics['hhi']:.4f}  |  "
            f"Diversification Score: {analytics['diversification_score']}/100\n"
            f"  Largest position: {analytics['max_single_asset_symbol']} "
            f"at {analytics['max_single_asset_pct']:.2f}%"
        )


    def _format_liquidity(self, analytics: dict) -> str:
        return (
            f"  Liquid reserve  : {analytics['liquid_pct']:.2f}%  "
            f"(min required: {MIN_LIQUIDITY_PCT}%)\n"
            f"  Illiquid exposure: {analytics['illiquid_pct']:.2f}%  "
            f"(max allowed: {MAX_ILLIQUID_PCT}%)"
        )


    def _build_fallback_result(
        self,
        hard_fail:          bool,
        violations:         list,
        constraint_summary: str,
        raw_output:         str,
    ) -> dict:
        approved = not hard_fail
        return {
            "approved":                 approved,
            "confidence_score":         0.6,
            "overall_rationale": (
                "AI evaluation output could not be fully parsed. "
                + ("Automatically rejected due to hard constraint violations. " if hard_fail else "")
                + f"Raw output excerpt: {raw_output[:400]}"
            ),
            "constraint_analysis":      constraint_summary,
            "risk_analysis":            "Unable to parse risk analysis from AI output.",
            "diversification_score":    50,
            "diversification_analysis": "Unable to parse diversification analysis.",
            "liquidity_assessment":     "Unable to parse liquidity assessment.",
            "objective_alignment":      "Unable to parse objective alignment.",
            "market_context_analysis":  "Unable to parse market context analysis.",
            "key_risks_introduced":     [],
            "key_risks_mitigated":      [],
            "recommendation":           "Manual review of this proposal is recommended.",
            "hard_constraint_fail":     hard_fail,
            "violations_count":         len(violations),
        }
