"""ALLOCENSUS — Phase 2: Genlayer Intelligent Contract"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("contracts/portfolio_rebalancing_rationale.py", '''\
# ALLOCENSUS — Portfolio Rebalancing Rationale Contract
# Genlayer Intelligent Contract
# Network: StudioNet | Token: GEN
# ------------------------------------------------------------------
# This contract evaluates whether a proposed portfolio rebalancing is
# justified, producing transparent, auditable, AI-driven investment
# reasoning. Multiple validators independently run the LLM evaluation;
# semantic consensus determines the final approved/rejected outcome.
# ------------------------------------------------------------------

from genlayer import *
import json


@gl.contract
class PortfolioRebalancingRationale:
    """
    Allocensus Portfolio Rebalancing Rationale Contract.

    Stores all evaluated proposals on-chain with their full rationale,
    constraint analysis, risk assessment, and validator consensus record.
    """

    # On-chain state
    proposals: TreeMap[str, dict]       # proposal_id -> full rationale record
    total_evaluations: u256             # lifetime counter
    owner: Address                      # contract deployer

    def __init__(self) -> None:
        self.proposals = TreeMap()
        self.total_evaluations = u256(0)
        self.owner = gl.message.sender_address

    # ── Read methods ─────────────────────────────────────────────────────────

    def get_proposal(self, proposal_id: str) -> dict:
        """Return full on-chain rationale record for a proposal."""
        return self.proposals.get(proposal_id, {})

    def get_total_evaluations(self) -> int:
        return int(self.total_evaluations)

    def get_owner(self) -> str:
        return str(self.owner)

    # ── Write method — the core non-deterministic evaluation ─────────────────

    @gl.public.write
    def evaluate_rebalancing(
        self,
        proposal_id: str,
        current_portfolio: str,       # JSON string
        proposed_portfolio: str,      # JSON string
        investor_profile: str,        # JSON string
        market_context: str,          # JSON string
    ) -> None:
        """
        Evaluate a portfolio rebalancing proposal using LLM-powered reasoning.

        This method is non-deterministic: each Genlayer validator independently
        runs the LLM evaluation. Semantic consensus across validators determines
        whether the rationale is approved or rejected.

        The evaluation covers:
        - Hard constraint compliance (8 rules from Allocensus constraint engine)
        - Risk alignment with investor profile
        - Diversification quality
        - Liquidity adequacy
        - Investment objective alignment
        - Market context appropriateness
        """
        current = json.loads(current_portfolio)
        proposed = json.loads(proposed_portfolio)
        profile = json.loads(investor_profile)
        market = json.loads(market_context)

        # ── Step 1: Fetch live market intelligence ────────────────────────────
        market_intel = self._fetch_market_intelligence(market)

        # ── Step 2: Run constraint pre-check ────────────────────────────────
        constraint_summary = self._check_constraints(proposed)

        # ── Step 3: LLM-powered rationale generation ─────────────────────────
        rationale = self._generate_rationale(
            current, proposed, profile, market, market_intel, constraint_summary
        )

        # ── Step 4: Persist result on-chain ──────────────────────────────────
        self.proposals[proposal_id] = rationale
        self.total_evaluations = self.total_evaluations + u256(1)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _fetch_market_intelligence(self, market_context: dict) -> str:
        """Fetch live market data for context-aware evaluation."""
        try:
            crypto_global = gl.get_webpage(
                "https://api.coingecko.com/api/v3/global",
                mode="text",
            )
            fear_greed = gl.get_webpage(
                "https://api.alternative.me/fng/?limit=1",
                mode="text",
            )
            return f"CoinGecko Global: {crypto_global[:800]}\nFear & Greed Index: {fear_greed[:200]}"
        except Exception:
            return "Live market data unavailable. Proceeding with provided context only."

    def _check_constraints(self, proposed: dict) -> str:
        """Build a human-readable constraint summary for the LLM prompt."""
        lines = []
        total = sum(proposed.values())
        lines.append(f"Total allocation: {total:.2f}% (must equal 100%)")

        max_single = max(proposed.values()) if proposed else 0
        lines.append(f"Highest single-asset concentration: {max_single:.2f}% (max 30%)")

        # Group by class if asset_classes embedded in keys
        lines.append(f"Number of assets in proposal: {len(proposed)}")

        constraint_status = "PASSES preliminary check" if abs(total - 100) <= 0.5 and max_single <= 30 else "FAILS preliminary check"
        lines.append(f"Preliminary constraint status: {constraint_status}")
        return "\n".join(lines)

    def _generate_rationale(
        self,
        current: dict,
        proposed: dict,
        profile: dict,
        market: dict,
        market_intel: str,
        constraint_summary: str,
    ) -> dict:
        """
        LLM-powered portfolio evaluation. Non-deterministic — validators
        independently evaluate and reach semantic consensus.
        """
        risk_tolerance = profile.get("risk_tolerance", "moderate")
        investment_horizon = profile.get("investment_horizon", "long")
        objectives = profile.get("investment_objectives", [])
        liquidity_req = profile.get("liquidity_requirements", "standard")

        current_str = json.dumps(current, indent=2)
        proposed_str = json.dumps(proposed, indent=2)

        prompt = f"""You are a senior portfolio risk analyst at an institutional asset management firm.
Your task is to evaluate a proposed portfolio rebalancing for an institutional client.

INVESTOR PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Horizon: {investment_horizon}
- Investment Objectives: {", ".join(objectives) if objectives else "Not specified"}
- Liquidity Requirements: {liquidity_req}

CURRENT PORTFOLIO ALLOCATIONS (% weight):
{current_str}

PROPOSED PORTFOLIO ALLOCATIONS (% weight):
{proposed_str}

PORTFOLIO CONSTRAINT STATUS:
{constraint_summary}

LIVE MARKET INTELLIGENCE:
{market_intel}

ADDITIONAL MARKET CONTEXT PROVIDED:
- Volatility Indicator: {market.get("volatility_indicator", "Not provided")}
- Macro Signals: {market.get("macro_signals", "Not provided")}
- Market Regime: {market.get("market_regime", "Not provided")}
- Additional Context: {market.get("additional_context", "Not provided")}

EVALUATION FRAMEWORK:
You must evaluate the rebalancing across 6 dimensions:

1. CONSTRAINT COMPLIANCE: Does the proposed allocation respect all hard rules?
   - Max 30% in any single asset
   - Max 60% in any single asset class
   - Min 5% liquidity reserve (stablecoins/cash)
   - Max 25% illiquid assets (DeFi + illiquid RWA combined)
   - Min 3 asset classes represented
   - No negative (leveraged) positions
   - Max 15% in any single DeFi protocol

2. RISK ALIGNMENT: Is the proposed risk level appropriate for this investor's risk tolerance and horizon?

3. DIVERSIFICATION QUALITY: Score 0-100. Does the rebalance improve or worsen cross-asset diversification?

4. LIQUIDITY ASSESSMENT: Does the portfolio maintain sufficient liquidity for this investor's stated requirements?

5. OBJECTIVE ALIGNMENT: Does the proposed allocation serve the investor's stated investment objectives?

6. MARKET CONTEXT APPROPRIATENESS: Given current market conditions, is this rebalancing timely and prudent?

IMPORTANT GUIDELINES:
- Be rigorous and specific. Reference actual allocation percentages.
- A rebalancing that violates hard constraints MUST be rejected.
- A rebalancing that technically passes constraints can still be rejected if it is imprudent.
- Multiple valid investment perspectives exist. Your judgment should be well-reasoned and defensible.
- Institutional-grade language is expected.

Respond with ONLY valid JSON in this exact structure:
{{
  "approved": true or false,
  "confidence_score": 0.0 to 1.0,
  "rationale": "2-4 paragraph overall rationale explaining the decision",
  "risk_analysis": "Specific analysis of risk changes introduced by this rebalance",
  "constraint_analysis": "Analysis of constraint compliance — which pass, which fail, any borderline cases",
  "diversification_score": 0 to 100,
  "liquidity_assessment": "Assessment of liquidity adequacy",
  "objective_alignment": "How well this rebalance serves the investor objectives",
  "key_risks_introduced": ["risk1", "risk2"],
  "key_risks_mitigated": ["risk1", "risk2"],
  "recommendation": "One sentence actionable recommendation"
}}"""

        result_str = gl.exec_prompt(prompt)
        result_str = result_str.strip()

        # Extract JSON from response
        start = result_str.find("{")
        end = result_str.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = result_str[start:end]
            try:
                result = json.loads(json_str)
            except Exception:
                result = {
                    "approved": False,
                    "confidence_score": 0.0,
                    "rationale": result_str,
                    "risk_analysis": "Parse error — see raw rationale",
                    "constraint_analysis": constraint_summary,
                    "diversification_score": 50,
                    "liquidity_assessment": "Unable to parse",
                    "objective_alignment": "Unable to parse",
                    "key_risks_introduced": [],
                    "key_risks_mitigated": [],
                    "recommendation": "Review manually",
                }
        else:
            result = {
                "approved": False,
                "confidence_score": 0.0,
                "rationale": result_str or "No output from LLM",
                "constraint_analysis": constraint_summary,
                "risk_analysis": "",
                "diversification_score": 0,
                "liquidity_assessment": "",
                "objective_alignment": "",
                "key_risks_introduced": [],
                "key_risks_mitigated": [],
                "recommendation": "Manual review required",
            }

        result["proposal_evaluated"] = True
        result["market_context_used"] = bool(market_intel)
        result["constraint_summary"] = constraint_summary
        return result
''')

write("contracts/README.md", """\
# Allocensus Intelligent Contract

## Overview
`portfolio_rebalancing_rationale.py` is the Genlayer Intelligent Contract that powers
Allocensus's AI-validated portfolio rebalancing evaluation.

## Deployment

### Prerequisites
- Genlayer Studio installed and running
- GEN token funded wallet on StudioNet
- Contract file ready at `contracts/portfolio_rebalancing_rationale.py`

### Steps
1. Open Genlayer Studio
2. Connect to StudioNet network
3. Load `portfolio_rebalancing_rationale.py`
4. Deploy — note the contract address
5. Fund contract caller wallet with GEN tokens
6. Set `GENLAYER_CONTRACT_ADDRESS=<address>` in `backend/.env`

## Key Method
```python
evaluate_rebalancing(
    proposal_id: str,
    current_portfolio: str,    # JSON
    proposed_portfolio: str,   # JSON
    investor_profile: str,     # JSON
    market_context: str,       # JSON
) -> None
```

## Validator Consensus
Each Genlayer validator independently:
1. Fetches live market data via `gl.get_webpage()`
2. Runs the LLM prompt via `gl.exec_prompt()`
3. Produces a structured JSON rationale

Semantic similarity across validator outputs determines final consensus.

## Network
- Network: StudioNet
- Fee token: GEN
- Chain ID: 61999
""")

write("contracts/deploy_instructions.md", """\
# Deployment Instructions

## 1. Open Genlayer Studio
Visit the Genlayer Studio web interface and connect your wallet.

## 2. Select StudioNet
Ensure you are connected to the StudioNet network (not a local simulator).

## 3. Fund Your Wallet
Obtain GEN tokens from the StudioNet faucet for transaction fees.

## 4. Deploy Contract
- Upload `portfolio_rebalancing_rationale.py`
- Click Deploy
- Wait for confirmation
- Copy the contract address

## 5. Configure Backend
```bash
# backend/.env
GENLAYER_CONTRACT_ADDRESS=0x...your_deployed_address...
GENLAYER_DEPLOYER_PRIVATE_KEY=0x...your_wallet_private_key...
```

## 6. Test Deployment
```bash
cd backend
python -c "
import asyncio
from app.services.genlayer_service import genlayer_service
async def test():
    result = await genlayer_service._rpc('eth_blockNumber', [])
    print('Connected:', result)
asyncio.run(test())
"
```

## 7. Verify Contract
After deploying, call `get_total_evaluations()` — should return 0.
""")

print("✅ Genlayer Intelligent Contract complete.")
print("   File: contracts/portfolio_rebalancing_rationale.py")
print("   Deploy this to Genlayer Studio → StudioNet, then provide the contract address.")
