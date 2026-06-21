# Deploying the Allocensus Intelligent Contract

## File
`contracts/portfolio_rebalancing_rationale.py`

## Steps

1. **Open Genlayer Studio**
   - Visit https://studio.genlayer.com
   - Connect your wallet (funded with GEN on StudioNet)

2. **Load the contract**
   - Click "New Contract"
   - Upload `contracts/portfolio_rebalancing_rationale.py`

3. **Deploy**
   - Click Deploy
   - Confirm GEN fee transaction
   - Wait for StudioNet confirmation
   - Copy the deployed contract address

4. **Configure backend**
   ```bash
   # backend/.env
   GENLAYER_CONTRACT_ADDRESS=0x<your_address_here>
   GENLAYER_DEPLOYER_PRIVATE_KEY=0x<your_pk>
   ```

5. **Verify deployment**
   ```bash
   cd backend
   python -c "
   from app.services.genlayer_service import genlayer_service
   import asyncio
   async def test():
       r = await genlayer_service._rpc('eth_blockNumber', [])
       print('Block:', r)
   asyncio.run(test())
   "
   ```

6. **Provide contract address**
   Once deployed, provide the contract address and it will be integrated.
