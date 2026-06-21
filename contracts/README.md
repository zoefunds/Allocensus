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
