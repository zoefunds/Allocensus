# Team Review Remediation Log

This document records the production changes made to address the team review findings and the deployment migration work that followed.

## Scope Completed

- Backend/frontend/contract synchronization
- Security review remediation
- New Fly.io backend deployment
- New Fly managed PostgreSQL deployment
- Frontend redeploy to Vercel
- Contract stake/payable flow implementation
- Production documentation updates

## Review Findings

### 1. Proposal results not securely bound to the transaction and submitting user

Fixed by recording transaction context in the backend proposal model and response flow.

Implemented:
- `proposal_id`
- `wallet_address`
- authenticated `user_id`
- `tx_hash`
- `block_number`
- `timestamp`
- `proposal_version`

Additional controls:
- proposal endpoints now enforce ownership
- claim/rebalance actions are tied to the authenticated wallet/user

### 2. Malformed AI output could fail open as approval

Fixed by changing rationale processing to fail closed.

Implemented:
- strict schema validation
- invalid JSON rejects the result
- missing fields reject the result
- invalid confidence score rejects the result
- unexpected structure rejects the result
- no implicit approval on malformed output

### 3. Individual proposal endpoints lacked ownership enforcement

Fixed by adding ownership checks to proposal read/write endpoints.

Protected endpoints include:
- get proposal
- proposal status / rationale
- update / delete
- history / transactions / rebalance-related actions

### 4. Displayed investment rules differed from enforced rules

Fixed by creating a single source of truth for investment rules in the backend and consuming them in the frontend.

Implemented:
- backend rules endpoint
- frontend reads rules from backend
- no hardcoded frontend rule values
- contract metadata aligned with backend rules

## Stake / Payable Flow

Added a user-paid transaction flow:
- each rebalance requires exactly `1 GEN`
- the user signs and pays from their own wallet
- the contract records the stake in proposal state
- the user can claim back `50%` of the stake after processing

Frontend updates:
- stake requirement shown on proposal creation
- stake requirement shown in submission modal
- claim page added for the refund path

## Infrastructure Migration

New production resources:
- Fly app: `allocensus-backend-zoe`
- Fly Postgres: `allocensus-db-zoe`

Production URLs:
- Frontend: `https://allocensus.vercel.app`
- Backend: `https://allocensus-backend-zoe.fly.dev`

## Contract Address

New contract address:
- `0x3FFd310A76C7caa09a3b30E4dbdDbADCbdFd69c6`

## Notes

- The backend database schema was migrated on the new Fly Postgres cluster.
- Frontend production deploy was corrected to use `frontend/` as the build root.
- README and deployment documentation were updated to reflect the new production setup.
