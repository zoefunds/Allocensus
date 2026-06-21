import httpx
import asyncio
import structlog
from app.config import settings
import json

log = structlog.get_logger()


class GenLayerService:
    def __init__(self):
        self.rpc_url        = settings.GENLAYER_RPC_URL
        self.contract_address = settings.GENLAYER_CONTRACT_ADDRESS

    async def _rpc(self, method: str, params: list) -> dict:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.rpc_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    def build_call_data(
        self,
        proposal_id:        str,
        current_allocations: dict,
        proposed_allocations: dict,
        asset_classes:       dict,
        investor_profile:    dict,
        market_context:      dict,
    ) -> dict:
        """
        Build the transaction call data for evaluate_rebalancing.
        This is returned to the frontend so the user signs it themselves.
        The backend never holds or uses any private key.
        """
        if not self.contract_address:
            raise ValueError("GENLAYER_CONTRACT_ADDRESS not configured")

        return {
            "to":     self.contract_address,
            "method": "evaluate_rebalancing",
            "args": {
                "proposal_id":        proposal_id,
                "current_portfolio":  json.dumps(current_allocations),
                "proposed_portfolio": json.dumps(proposed_allocations),
                "asset_classes":      json.dumps(asset_classes),
                "investor_profile":   json.dumps(investor_profile),
                "market_context":     json.dumps(market_context),
            },
        }

    async def poll_transaction_result(self, tx_hash: str, max_wait: int = 120) -> dict | None:
        """Poll for transaction receipt until confirmed or timeout."""
        for _ in range(max_wait // 5):
            try:
                result = await self._rpc("eth_getTransactionReceipt", [tx_hash])
                receipt = result.get("result")
                if receipt:
                    return receipt
            except Exception:
                pass
            await asyncio.sleep(5)
        return None

    async def read_rationale(self, tx_hash: str) -> dict | None:
        """Read the evaluation result stored by the contract after consensus."""
        try:
            result = await self._rpc("gen_getContractResult", [tx_hash])
            return result.get("result")
        except Exception as e:
            log.error("genlayer_read_failed", error=str(e))
            return None


genlayer_service = GenLayerService()
