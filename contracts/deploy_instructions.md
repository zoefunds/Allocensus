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
