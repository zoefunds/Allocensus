"""ALLOCENSUS — Backend Services"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

write("backend/app/services/__init__.py", "")

write("backend/app/services/wallet_service.py", '''\
from eth_account import Account
from mnemonic import Mnemonic
from app.utils.security import encrypt_private_key, decrypt_private_key
from app.models.wallet import Wallet, EncryptedKeystore
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

Account.enable_unaudited_hdwallet_features()
mnemo = Mnemonic("english")


async def create_wallet_for_user(user: User, hashed_password: str, db: AsyncSession) -> Wallet:
    """Generate HD wallet, encrypt private key, persist wallet + keystore."""
    mnemonic_phrase = mnemo.generate(strength=128)
    account = Account.from_mnemonic(mnemonic_phrase, account_path="m/44'/60'/0'/0/0")

    wallet = Wallet(
        user_id=user.id,
        address=account.address,
        derivation_path="m/44'/60'/0'/0/0",
        chain_id=61999,
    )
    db.add(wallet)
    await db.flush()

    encrypted_pk = encrypt_private_key(account.key.hex(), hashed_password)
    encrypted_mn = encrypt_private_key(mnemonic_phrase, hashed_password)

    keystore = EncryptedKeystore(
        wallet_id=wallet.id,
        encrypted_private_key=encrypted_pk,
        encrypted_mnemonic=encrypted_mn,
    )
    db.add(keystore)
    return wallet


async def export_private_key(wallet: Wallet, password: str, hashed_password: str) -> str:
    """Decrypt and return private key hex — requires valid password verification."""
    if not wallet.keystore:
        raise ValueError("No keystore found for this wallet")
    return decrypt_private_key(wallet.keystore.encrypted_private_key, hashed_password)


async def get_signer_account(wallet: Wallet, hashed_password: str) -> object:
    """Return eth_account Account object for signing Genlayer transactions."""
    pk_hex = decrypt_private_key(wallet.keystore.encrypted_private_key, hashed_password)
    return Account.from_key(pk_hex)
''')

write("backend/app/services/auth_service.py", '''\
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.models.wallet import Wallet
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.utils.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    generate_secure_token,
)
from app.services.wallet_service import create_wallet_for_user
from app.services.notification_service import send_verification_email
import uuid


async def register_user(req: RegisterRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed = hash_password(req.password)
    verification_token = generate_secure_token()

    user = User(
        email=req.email,
        hashed_password=hashed,
        full_name=req.full_name,
        role=UserRole.ANALYST,
        email_verification_token=verification_token,
    )
    db.add(user)
    await db.flush()

    wallet = await create_wallet_for_user(user, hashed, db)
    await db.flush()

    await send_verification_email(user.email, verification_token)

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role.value,
        wallet_address=wallet.address,
    )


async def login_user(req: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = wallet_result.scalar_one_or_none()

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role.value,
        wallet_address=wallet.address if wallet else None,
    )
''')

write("backend/app/services/portfolio_service.py", '''\
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.portfolio import Portfolio, PortfolioAsset, PortfolioSnapshot
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from app.utils.constraints import validate_portfolio_constraints
import uuid
from datetime import datetime, timezone


async def get_portfolio_or_404(portfolio_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Portfolio:
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets))
        .where(Portfolio.id == portfolio_id, Portfolio.owner_id == user_id, Portfolio.is_active == True)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return p


async def create_portfolio(req: PortfolioCreate, user_id: uuid.UUID, db: AsyncSession) -> Portfolio:
    portfolio = Portfolio(
        owner_id=user_id,
        name=req.name,
        description=req.description,
        currency=req.currency,
        investor_profile_id=req.investor_profile_id,
    )
    db.add(portfolio)
    await db.flush()

    total_value = 0.0
    for asset_in in req.assets:
        value = asset_in.quantity * asset_in.current_price_usd
        total_value += value
        asset = PortfolioAsset(
            portfolio_id=portfolio.id,
            **asset_in.model_dump(),
            current_value_usd=value,
        )
        db.add(asset)

    portfolio.total_value_usd = total_value
    await db.flush()

    snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value_usd=total_value,
        allocations={a.symbol: a.target_weight_pct for a in portfolio.assets},
    )
    db.add(snapshot)
    return portfolio


async def recalculate_weights(portfolio: Portfolio) -> None:
    total = sum(a.current_value_usd for a in portfolio.assets)
    portfolio.total_value_usd = total
    for asset in portfolio.assets:
        asset.current_weight_pct = (asset.current_value_usd / total * 100) if total > 0 else 0.0


async def check_drift(portfolio: Portfolio) -> list[dict]:
    """Return list of assets whose current weight drifts >5% from target."""
    drifts = []
    for asset in portfolio.assets:
        drift = abs(asset.current_weight_pct - asset.target_weight_pct)
        if drift >= 5.0:
            drifts.append({
                "symbol": asset.symbol,
                "current": asset.current_weight_pct,
                "target": asset.target_weight_pct,
                "drift": drift,
            })
    return drifts
''')

write("backend/app/services/notification_service.py", '''\
import resend
import structlog
from app.config import settings

log = structlog.get_logger()

resend.api_key = settings.RESEND_API_KEY


async def send_verification_email(email: str, token: str) -> None:
    if not settings.RESEND_API_KEY:
        log.info("email_skipped_no_key", email=email)
        return
    try:
        verify_url = f"{settings.APP_ENV == 'production' and 'https://allocensus.com' or 'http://localhost:3000'}/verify-email?token={token}"
        resend.Emails.send({
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": email,
            "subject": "Verify your Allocensus account",
            "html": f"""
            <h2>Welcome to Allocensus</h2>
            <p>Please verify your email address to activate your account and wallet.</p>
            <a href="{verify_url}" style="background:#0ea5e9;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;">Verify Email</a>
            <p>This link expires in 24 hours.</p>
            """,
        })
    except Exception as e:
        log.error("email_send_failed", email=email, error=str(e))


async def send_rationale_ready_email(email: str, proposal_id: str, approved: bool) -> None:
    if not settings.RESEND_API_KEY:
        return
    try:
        status_word = "APPROVED" if approved else "REJECTED"
        color = "#10b981" if approved else "#ef4444"
        resend.Emails.send({
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
            "to": email,
            "subject": f"Rebalancing Proposal {status_word} — Allocensus",
            "html": f"""
            <h2>Rebalancing Proposal {status_word}</h2>
            <p>Your portfolio rebalancing proposal has been evaluated by the Genlayer network.</p>
            <p style="color:{color};font-weight:bold;font-size:18px;">Result: {status_word}</p>
            <p>View the full AI rationale and validator consensus in your dashboard.</p>
            <a href="http://localhost:3000/rebalancing/{proposal_id}">View Rationale →</a>
            """,
        })
    except Exception as e:
        log.error("rationale_email_failed", error=str(e))
''')

write("backend/app/services/price_service.py", '''\
import httpx
import redis.asyncio as aioredis
import json
from app.config import settings
import structlog

log = structlog.get_logger()
CACHE_TTL = 60  # seconds


async def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_crypto_prices(coingecko_ids: list[str]) -> dict[str, float]:
    """Fetch USD prices from CoinGecko. Redis-cached for 60 seconds."""
    if not coingecko_ids:
        return {}
    cache_key = f"prices:cg:{','.join(sorted(coingecko_ids))}"
    try:
        r = await _get_redis()
        cached = await r.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    try:
        ids_param = ",".join(coingecko_ids)
        headers = {"x-cg-demo-api-key": settings.COINGECKO_API_KEY} if settings.COINGECKO_API_KEY else {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ids_param, "vs_currencies": "usd"},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            prices = {coin_id: info["usd"] for coin_id, info in data.items()}
            try:
                r = await _get_redis()
                await r.setex(cache_key, CACHE_TTL, json.dumps(prices))
            except Exception:
                pass
            return prices
    except Exception as e:
        log.error("price_fetch_failed", error=str(e))
        return {}


async def get_market_context() -> dict:
    """Fetch basic market context for the Genlayer contract call."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/global",
                headers={"x-cg-demo-api-key": settings.COINGECKO_API_KEY} if settings.COINGECKO_API_KEY else {},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "total_market_cap_usd": data.get("total_market_cap", {}).get("usd"),
                "market_cap_change_24h": data.get("market_cap_change_percentage_24h_usd"),
                "btc_dominance": data.get("market_cap_percentage", {}).get("btc"),
                "active_cryptocurrencies": data.get("active_cryptocurrencies"),
            }
    except Exception:
        return {}
''')

write("backend/app/services/genlayer_service.py", '''\
import httpx
import asyncio
import structlog
from app.config import settings
from app.models.rebalancing import RebalancingProposal, ProposalStatus, RationaleResult
from sqlalchemy.ext.asyncio import AsyncSession
import json

log = structlog.get_logger()


class GenLayerService:
    def __init__(self):
        self.rpc_url = settings.GENLAYER_RPC_URL
        self.contract_address = settings.GENLAYER_CONTRACT_ADDRESS

    async def _rpc(self, method: str, params: list) -> dict:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.rpc_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def submit_rebalancing_proposal(
        self,
        proposal: RebalancingProposal,
        investor_profile: dict,
        private_key_hex: str,
    ) -> str:
        """
        Call the Genlayer Intelligent Contract to evaluate the rebalancing proposal.
        Returns the transaction hash.
        """
        if not self.contract_address:
            raise ValueError("GENLAYER_CONTRACT_ADDRESS not configured")

        from eth_account import Account
        account = Account.from_key(private_key_hex)

        call_data = {
            "current_portfolio": proposal.current_allocations,
            "proposed_portfolio": proposal.proposed_allocations,
            "investor_profile": investor_profile,
            "market_context": proposal.market_context,
        }

        try:
            result = await self._rpc("eth_sendTransaction", [{
                "from": account.address,
                "to": self.contract_address,
                "data": json.dumps(call_data),
                "gas": "0x0",
            }])
            tx_hash = result.get("result", "")
            log.info("genlayer_tx_submitted", tx_hash=tx_hash, proposal_id=str(proposal.id))
            return tx_hash
        except Exception as e:
            log.error("genlayer_submit_failed", error=str(e), proposal_id=str(proposal.id))
            raise

    async def poll_transaction_result(self, tx_hash: str, max_wait: int = 120) -> dict | None:
        """Poll for transaction receipt until confirmed or timeout."""
        for attempt in range(max_wait // 5):
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
        """Read the rationale output stored by the contract after consensus."""
        try:
            result = await self._rpc("gen_getContractResult", [tx_hash])
            return result.get("result")
        except Exception as e:
            log.error("genlayer_read_failed", error=str(e))
            return None


genlayer_service = GenLayerService()
''')

write("backend/app/services/rebalancing_service.py", '''\
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.rebalancing import RebalancingProposal, RationaleResult, ProposalStatus
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.rebalancing import ProposalCreate
from app.utils.constraints import validate_portfolio_constraints
from app.services.genlayer_service import genlayer_service
from app.services.notification_service import send_rationale_ready_email
from app.services.price_service import get_market_context
import uuid
import structlog

log = structlog.get_logger()


async def create_proposal(
    req: ProposalCreate,
    user: User,
    db: AsyncSession,
) -> RebalancingProposal:
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.assets))
        .where(Portfolio.id == req.portfolio_id, Portfolio.owner_id == user.id)
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    current_allocs = {a.symbol: a.current_weight_pct for a in portfolio.assets}
    asset_classes = {a.symbol: a.asset_class for a in portfolio.assets}

    violations = validate_portfolio_constraints(req.proposed_allocations, asset_classes)

    market_ctx = await get_market_context()
    market_ctx.update(req.market_context.model_dump(exclude_none=True))

    proposal = RebalancingProposal(
        portfolio_id=req.portfolio_id,
        submitted_by=user.id,
        current_allocations=current_allocs,
        proposed_allocations=req.proposed_allocations,
        market_context=market_ctx,
        constraint_violations=[v.__dict__ for v in violations],
        notes=req.notes,
        status=ProposalStatus.DRAFT,
    )
    db.add(proposal)
    return proposal


async def submit_to_genlayer(
    proposal: RebalancingProposal,
    investor_profile: dict,
    private_key_hex: str,
    user_email: str,
    db: AsyncSession,
) -> RebalancingProposal:
    if proposal.constraint_violations:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Proposal violates portfolio constraints",
                "violations": proposal.constraint_violations,
            },
        )

    proposal.status = ProposalStatus.SUBMITTED
    await db.flush()

    try:
        tx_hash = await genlayer_service.submit_rebalancing_proposal(
            proposal, investor_profile, private_key_hex
        )
        proposal.genlayer_tx_hash = tx_hash
        proposal.status = ProposalStatus.PENDING_CONSENSUS
        log.info("proposal_submitted", proposal_id=str(proposal.id), tx_hash=tx_hash)
    except Exception as e:
        proposal.status = ProposalStatus.FAILED
        log.error("proposal_submit_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Genlayer submission failed: {e}")

    return proposal


async def process_rationale_result(
    proposal: RebalancingProposal,
    raw_result: dict,
    user_email: str,
    db: AsyncSession,
) -> RationaleResult:
    """Parse Genlayer contract output and persist rationale result."""
    approved = raw_result.get("approved", False)

    rationale = RationaleResult(
        proposal_id=proposal.id,
        approved=approved,
        confidence_score=raw_result.get("confidence_score"),
        rationale_text=raw_result.get("rationale", ""),
        risk_analysis=raw_result.get("risk_analysis"),
        constraint_analysis=raw_result.get("constraint_analysis"),
        diversification_score=raw_result.get("diversification_score"),
        liquidity_assessment=raw_result.get("liquidity_assessment"),
        objective_alignment=raw_result.get("objective_alignment"),
        validator_consensus=raw_result.get("validator_consensus", {}),
        raw_contract_output=raw_result,
    )
    db.add(rationale)

    proposal.status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
    await db.flush()

    await send_rationale_ready_email(user_email, str(proposal.id), approved)
    return rationale
''')

write("backend/app/services/audit_service.py", '''\
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditEvent, AuditEventType, ComplianceLog
from app.models.rebalancing import RebalancingProposal
import uuid
import structlog

log = structlog.get_logger()


async def log_event(
    db: AsyncSession,
    event_type: AuditEventType,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
    on_chain_ref: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {},
        on_chain_ref=on_chain_ref,
    )
    db.add(event)
    log.info("audit_event", type=event_type.value, user_id=str(user_id), resource=resource_id)
    return event


async def log_compliance(
    db: AsyncSession,
    check_type: str,
    passed: bool,
    portfolio_id: uuid.UUID | None = None,
    proposal_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> ComplianceLog:
    entry = ComplianceLog(
        portfolio_id=portfolio_id,
        proposal_id=proposal_id,
        check_type=check_type,
        passed=passed,
        details=details or {},
    )
    db.add(entry)
    return entry
''')

print("✅ Services complete.")
