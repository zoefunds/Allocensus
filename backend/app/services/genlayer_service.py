import httpx
import json
import structlog
from app.config import settings

log = structlog.get_logger()


# ─── Genlayer calldata encoding (matches genlayer-js abi.calldata) ───────────

def _varint(n: int) -> bytes:
    if n == 0:
        return b"\x00"
    result = []
    while n > 0:
        cur = n & 0x7F
        n >>= 7
        if n > 0:
            cur |= 0x80
        result.append(cur)
    return bytes(result)

def _gl_string(s: str) -> bytes:
    b = s.encode("utf-8")
    return _varint((len(b) << 3) | 4) + b  # TYPE_STR = 4

def _gl_map_key(s: str) -> bytes:
    b = s.encode("utf-8")
    return _varint(len(b)) + b  # map keys: raw length prefix, no type tag

def _gl_calldata(method: str, kwargs: dict) -> bytes:
    # Build {method, kwargs} map — genlayer sorts map keys alphabetically
    parts: list[bytes] = []
    parts.append(_varint((2 << 3) | 6))  # MAP(2), TYPE_MAP = 6

    # "kwargs" < "method" alphabetically → kwargs entry comes first
    parts.append(_gl_map_key("kwargs"))
    nested = sorted(kwargs.items())
    parts.append(_varint((len(nested) << 3) | 6))  # nested MAP
    for k, v in nested:
        parts.append(_gl_map_key(k))
        parts.append(_gl_string(str(v)))

    parts.append(_gl_map_key("method"))
    parts.append(_gl_string(method))

    return b"".join(parts)


def _rlp_read_request(calldata: bytes) -> str:
    """RLP-encode [calldata, false] for gen_call (matches genlayer-js transactions.serialize)."""
    n = len(calldata)
    if n < 56:
        cd_rlp = bytes([0x80 + n]) + calldata
    else:
        nb = n.to_bytes((n.bit_length() + 7) // 8, "big")
        cd_rlp = bytes([0xB7 + len(nb)]) + nb + calldata

    payload = cd_rlp + b"\x00"  # false boolean = 0x00 in RLP
    p = len(payload)
    if p < 56:
        prefix = bytes([0xC0 + p])
    else:
        pb = p.to_bytes((p.bit_length() + 7) // 8, "big")
        prefix = bytes([0xF7 + len(pb)]) + pb

    return "0x" + (prefix + payload).hex()


def _decode_gl_result(hex_result: str) -> str:
    """Strip genlayer result prefix bytes and return the JSON string."""
    raw = bytes.fromhex(hex_result[2:] if hex_result.startswith("0x") else hex_result)
    start = raw.find(b"{")
    if start < 0:
        raise ValueError(f"No JSON in gen_call result: {hex_result[:80]}")
    return raw[start:].decode("utf-8")


# ─── Service ─────────────────────────────────────────────────────────────────

class GenLayerService:
    def __init__(self):
        self.rpc_url          = settings.GENLAYER_RPC_URL
        self.contract_address = settings.GENLAYER_CONTRACT_ADDRESS

    async def _rpc(self, method: str, params: list) -> dict:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.rpc_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    def build_call_data(
        self,
        proposal_id:          str,
        current_allocations:  dict,
        proposed_allocations: dict,
        asset_classes:        dict,
        investor_profile:     dict,
        market_context:       dict,
    ) -> dict:
        """
        Return unsigned tx call data for evaluate_rebalancing.
        Frontend signs with the user's own private key — backend never touches keys.
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

    async def is_tx_finalized(self, tx_hash: str) -> bool:
        """Return True when the Genlayer tx has status FINALIZED."""
        try:
            result = await self._rpc("eth_getTransactionByHash", [tx_hash])
            tx = result.get("result")
            return bool(tx) and str(tx.get("status", "")).upper() == "FINALIZED"
        except Exception as e:
            log.warning("genlayer_status_check_failed", tx=tx_hash, error=str(e))
            return False

    async def read_rationale(self, tx_hash: str, proposal_id: str) -> dict | None:
        """
        Check tx is FINALIZED, then read the stored evaluation from on-chain state
        via gen_call → get_proposal(proposal_id).
        Returns parsed evaluation dict, or None if not yet finalized.
        """
        if not await self.is_tx_finalized(tx_hash):
            return None

        calldata = _gl_calldata("get_proposal", {"proposal_id": proposal_id})
        data_hex = _rlp_read_request(calldata)

        params = [{
            "type": "read",
            "to":   self.contract_address,
            "from": "0x0000000000000000000000000000000000000000",
            "data": data_hex,
            "transaction_hash_variant": "latest-nonfinal",
        }]

        try:
            result   = await self._rpc("gen_call", params)
            hex_data = result.get("result", "")
            if not hex_data:
                log.error("gen_call_empty_result", proposal_id=proposal_id)
                return None
            raw_json = _decode_gl_result(hex_data)
            parsed   = json.loads(raw_json)
            if not parsed or "approved" not in parsed:
                return None
            return parsed
        except Exception as e:
            log.error("gen_call_failed", proposal_id=proposal_id, error=str(e))
            return None


genlayer_service = GenLayerService()
