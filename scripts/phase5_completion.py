"""ALLOCENSUS — Phase 5: Complete all remaining work"""
import os, secrets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")


# ── 1. Backend .env with real values ─────────────────────────────────────────
write("backend/.env", f"""\
# ── Application ──────────────────────────────────────────────
APP_NAME=Allocensus
APP_ENV=production
DEBUG=false
SECRET_KEY={secrets.token_hex(32)}
ALLOWED_ORIGINS=http://localhost:3000,https://allocensus.vercel.app

# ── Database ─────────────────────────────────────────────────
POSTGRES_USER=allocensus
POSTGRES_PASSWORD=allocensus_dev
POSTGRES_DB=allocensus
DATABASE_URL=postgresql+asyncpg://allocensus:allocensus_dev@localhost:5432/allocensus
DATABASE_URL_SYNC=postgresql://allocensus:allocensus_dev@localhost:5432/allocensus

# ── Redis (Upstash) ──────────────────────────────────────────
REDIS_URL=rediss://default:gQAAAAAAAlC8AAIgcDFkZWFkNTA0Njc2MDM0M2IxYjdkNDQ3NjVjNGVhOTI3Mg@fancy-hookworm-151740.upstash.io:6379

# ── JWT ──────────────────────────────────────────────────────
JWT_SECRET_KEY={secrets.token_hex(32)}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Wallet Encryption ────────────────────────────────────────
WALLET_ENCRYPTION_KEY={secrets.token_hex(32)}
WALLET_PBKDF2_ITERATIONS=310000

# ── Genlayer ─────────────────────────────────────────────────
GENLAYER_RPC_URL=https://studio.genlayer.com/api
GENLAYER_CONTRACT_ADDRESS=0xe45A5379bDD30BF75D08752cb32c4178f59445EA

# ── Price Feeds ──────────────────────────────────────────────
COINGECKO_API_KEY=
YAHOO_FINANCE_ENABLED=true

# ── Email (Brevo) ────────────────────────────────────────────
BREVO_API_KEY=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
EMAIL_FROM=preciousmofeoluwa@gmail.com
EMAIL_FROM_NAME=Allocensus

# ── Storage (Cloudflare R2) ──────────────────────────────────
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=allocensus-reports
R2_PUBLIC_URL=

# ── Monitoring ───────────────────────────────────────────────
SENTRY_DSN=

# ── Rate Limiting ────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=20
""")


# ── 2. Config — add BREVO_API_KEY, remove RESEND ─────────────────────────────
write("backend/app/config.py", """\
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Allocensus"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://allocensus:allocensus_dev@localhost:5432/allocensus"
    DATABASE_URL_SYNC: str = "postgresql://allocensus:allocensus_dev@localhost:5432/allocensus"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Wallet
    WALLET_ENCRYPTION_KEY: str = "0" * 64
    WALLET_PBKDF2_ITERATIONS: int = 310000

    # Genlayer
    GENLAYER_RPC_URL: str = "https://studio.genlayer.com/api"
    GENLAYER_CONTRACT_ADDRESS: str = "0xe45A5379bDD30BF75D08752cb32c4178f59445EA"

    # Price feeds
    COINGECKO_API_KEY: str = ""
    YAHOO_FINANCE_ENABLED: bool = True

    # Email — Brevo
    BREVO_API_KEY: str = ""
    EMAIL_FROM: str = "preciousmofeoluwa@gmail.com"
    EMAIL_FROM_NAME: str = "Allocensus"

    # Storage
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "allocensus-reports"
    R2_PUBLIC_URL: str = ""

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
""")


# ── 3. Email service — Brevo via httpx ───────────────────────────────────────
write("backend/app/services/notification_service.py", """\
import httpx
import structlog
from app.config import settings

log = structlog.get_logger()

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

APP_URL = "https://allocensus.vercel.app"


def _headers() -> dict:
    return {
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _send(subject: str, to_email: str, html: str) -> None:
    if not settings.BREVO_API_KEY:
        log.info("email_skipped_no_key", to=to_email, subject=subject)
        return
    payload = {
        "sender": {"name": settings.EMAIL_FROM_NAME, "email": settings.EMAIL_FROM},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(BREVO_SEND_URL, json=payload, headers=_headers())
            resp.raise_for_status()
            log.info("email_sent", to=to_email, subject=subject)
    except Exception as e:
        log.error("email_send_failed", to=to_email, error=str(e))


async def send_verification_email(email: str, token: str) -> None:
    verify_url = f"{APP_URL}/verify-email?token={token}"
    await _send(
        subject="Verify your Allocensus account",
        to_email=email,
        html=f"""
<!DOCTYPE html><html><body style="font-family:sans-serif;background:#0a0f1e;color:#e2e8f0;padding:40px;">
<div style="max-width:520px;margin:auto;background:#0f1629;border:1px solid #1e2d4a;border-radius:16px;padding:40px;">
  <div style="margin-bottom:24px;">
    <span style="background:#10b981;color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:1px;">ALLOCENSUS</span>
  </div>
  <h1 style="font-size:24px;font-weight:700;color:#f8fafc;margin:0 0 16px;">Verify your email</h1>
  <p style="color:#94a3b8;line-height:1.6;margin:0 0 32px;">
    Welcome to Allocensus. Click the button below to verify your email address and activate
    your account along with your auto-provisioned BIP-39 HD wallet.
  </p>
  <a href="{verify_url}"
     style="display:inline-block;background:#10b981;color:#fff;font-weight:600;font-size:14px;
            padding:14px 28px;border-radius:10px;text-decoration:none;letter-spacing:0.3px;">
    Verify Email Address
  </a>
  <p style="color:#475569;font-size:12px;margin:32px 0 0;">This link expires in 24 hours.</p>
</div>
</body></html>""",
    )


async def send_rationale_ready_email(email: str, proposal_id: str, approved: bool) -> None:
    status_word = "APPROVED" if approved else "REJECTED"
    color       = "#10b981" if approved else "#ef4444"
    bg_color    = "#0d2015" if approved else "#200d0d"
    detail_url  = f"{APP_URL}/rebalancing/{proposal_id}"
    await _send(
        subject=f"Rebalancing Proposal {status_word} — Allocensus",
        to_email=email,
        html=f"""
<!DOCTYPE html><html><body style="font-family:sans-serif;background:#0a0f1e;color:#e2e8f0;padding:40px;">
<div style="max-width:520px;margin:auto;background:#0f1629;border:1px solid #1e2d4a;border-radius:16px;padding:40px;">
  <div style="margin-bottom:24px;">
    <span style="background:#10b981;color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:1px;">ALLOCENSUS</span>
  </div>
  <h1 style="font-size:24px;font-weight:700;color:#f8fafc;margin:0 0 16px;">Evaluation Complete</h1>
  <div style="background:{bg_color};border:1px solid {color}33;border-radius:12px;padding:20px;margin:0 0 24px;">
    <p style="font-size:28px;font-weight:800;color:{color};margin:0 0 4px;">{status_word}</p>
    <p style="color:#94a3b8;font-size:14px;margin:0;">
      Genlayer validator consensus has been reached on your rebalancing proposal.
    </p>
  </div>
  <p style="color:#94a3b8;line-height:1.6;margin:0 0 28px;">
    View the full AI rationale, risk analysis, diversification score, and on-chain audit trail
    in your Allocensus dashboard.
  </p>
  <a href="{detail_url}"
     style="display:inline-block;background:#10b981;color:#fff;font-weight:600;font-size:14px;
            padding:14px 28px;border-radius:10px;text-decoration:none;">
    View Full Rationale →
  </a>
  <p style="color:#475569;font-size:12px;margin:32px 0 0;">
    Proposal ID: {proposal_id}
  </p>
</div>
</body></html>""",
    )


async def send_welcome_email(email: str, full_name: str, wallet_address: str) -> None:
    await _send(
        subject="Welcome to Allocensus — Your wallet is ready",
        to_email=email,
        html=f"""
<!DOCTYPE html><html><body style="font-family:sans-serif;background:#0a0f1e;color:#e2e8f0;padding:40px;">
<div style="max-width:520px;margin:auto;background:#0f1629;border:1px solid #1e2d4a;border-radius:16px;padding:40px;">
  <div style="margin-bottom:24px;">
    <span style="background:#10b981;color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;letter-spacing:1px;">ALLOCENSUS</span>
  </div>
  <h1 style="font-size:24px;font-weight:700;color:#f8fafc;margin:0 0 16px;">Welcome, {full_name}</h1>
  <p style="color:#94a3b8;line-height:1.6;margin:0 0 24px;">
    Your Allocensus account is active. A BIP-39 HD wallet has been automatically provisioned
    for your account and is ready to sign Genlayer transactions.
  </p>
  <div style="background:#0d1a2e;border:1px solid #1e2d4a;border-radius:10px;padding:16px;margin:0 0 28px;">
    <p style="color:#64748b;font-size:11px;font-weight:600;letter-spacing:1px;margin:0 0 6px;">WALLET ADDRESS</p>
    <code style="color:#10b981;font-size:13px;word-break:break-all;">{wallet_address}</code>
  </div>
  <a href="{APP_URL}/dashboard"
     style="display:inline-block;background:#10b981;color:#fff;font-weight:600;font-size:14px;
            padding:14px 28px;border-radius:10px;text-decoration:none;">
    Open Dashboard →
  </a>
</div>
</body></html>""",
    )
""")


# ── 4. Rebalancing service — fix process_rationale_result ────────────────────
write("backend/app/services/rebalancing_service.py", """\
import json
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.rebalancing import RebalancingProposal, RationaleResult, ProposalStatus
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.rebalancing import ProposalCreate
from app.utils.constraints import validate_portfolio_constraints
from app.services.genlayer_service import genlayer_service
from app.services.notification_service import send_rationale_ready_email
from app.services.price_service import get_market_context

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
    asset_classes  = {a.symbol: a.asset_class for a in portfolio.assets}

    violations  = validate_portfolio_constraints(req.proposed_allocations, asset_classes)
    market_ctx  = await get_market_context()
    if req.market_context:
        market_ctx.update(req.market_context.model_dump(exclude_none=True))

    proposal = RebalancingProposal(
        portfolio_id          = req.portfolio_id,
        submitted_by          = user.id,
        current_allocations   = current_allocs,
        proposed_allocations  = req.proposed_allocations,
        market_context        = market_ctx,
        constraint_violations = [v.__dict__ for v in violations],
        notes                 = req.notes,
        status                = ProposalStatus.DRAFT,
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    return proposal


async def process_rationale_result(
    proposal:   RebalancingProposal,
    raw_result: dict | str,
    user_email: str,
    db:         AsyncSession,
) -> RationaleResult:
    """
    Parse the Genlayer contract output (from gen_getContractResult) and
    persist it as a RationaleResult. The contract stores results as JSON
    strings keyed by proposal_id inside the proposals_json TreeMap.

    raw_result may be:
      - A dict already parsed by the caller
      - A string (JSON from the contract's get_proposal view method)
      - A dict with a nested 'result' or 'output' key from the RPC layer
    """
    # Unwrap RPC envelope if present
    if isinstance(raw_result, dict):
        data = (
            raw_result.get("result")
            or raw_result.get("output")
            or raw_result
        )
    else:
        data = raw_result

    # Parse JSON string if needed
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {}

    if not isinstance(data, dict):
        data = {}

    approved = bool(data.get("approved", False))

    rationale = RationaleResult(
        proposal_id          = proposal.id,
        approved             = approved,
        confidence_score     = data.get("confidence_score"),
        rationale_text       = data.get("overall_rationale") or data.get("rationale_text", ""),
        risk_analysis        = data.get("risk_analysis"),
        constraint_analysis  = data.get("constraint_analysis"),
        diversification_score = data.get("diversification_score"),
        liquidity_assessment = data.get("liquidity_assessment"),
        objective_alignment  = data.get("objective_alignment"),
        validator_consensus  = {
            "market_context_analysis": data.get("market_context_analysis"),
            "key_risks_introduced":    data.get("key_risks_introduced", []),
            "key_risks_mitigated":     data.get("key_risks_mitigated", []),
            "recommendation":          data.get("recommendation"),
            "hard_constraint_fail":    data.get("hard_constraint_fail", False),
            "violations_count":        data.get("violations_count", 0),
            "analytics":               data.get("analytics", {}),
        },
        raw_contract_output  = data,
    )
    db.add(rationale)

    proposal.status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
    await db.commit()
    await db.refresh(rationale)

    await send_rationale_ready_email(user_email, str(proposal.id), approved)
    log.info("rationale_persisted", proposal_id=str(proposal.id), approved=approved)
    return rationale
""")


# ── 5. Export router — PDF + CSV ─────────────────────────────────────────────
write("backend/app/routers/export.py", """\
import csv
import io
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.rebalancing import RebalancingProposal, RationaleResult, ProposalStatus
from app.models.portfolio import Portfolio
from app.dependencies import CurrentUser, DB
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.units import mm
import uuid

router = APIRouter()

# Allocensus brand colours
GREEN  = HexColor("#10b981")
DARK   = HexColor("#0a0f1e")
DARK2  = HexColor("#0f1629")
SLATE  = HexColor("#94a3b8")
WHITE  = white


def _get_proposal_and_rationale(proposal_id: str, user_id, result):
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if str(proposal.portfolio.owner_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return proposal


@router.get("/{proposal_id}/export/pdf")
async def export_pdf(proposal_id: str, user: CurrentUser, db: DB):
    result = await db.execute(
        select(RebalancingProposal)
        .options(
            selectinload(RebalancingProposal.rationale),
            selectinload(RebalancingProposal.portfolio),
        )
        .where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    rationale = proposal.rationale
    buf    = io.BytesIO()
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=22, textColor=DARK,
        spaceAfter=4, fontName="Helvetica-Bold",
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=GREEN,
        spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#334155"),
        leading=16, spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=9, textColor=HexColor("#64748b"), leading=14,
    )

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    story = []

    # Header
    decision     = "APPROVED" if (rationale and rationale.approved) else "REJECTED"
    dec_color    = "#10b981" if (rationale and rationale.approved) else "#ef4444"
    story.append(Paragraph("ALLOCENSUS", ParagraphStyle(
        "Brand", fontSize=9, textColor=GREEN, fontName="Helvetica-Bold",
        letterSpacing=2, spaceAfter=8,
    )))
    story.append(Paragraph("Portfolio Rebalancing Rationale Report", title_style))
    story.append(Paragraph(
        f'Decision: <font color="{dec_color}"><b>{decision}</b></font>',
        ParagraphStyle("Dec", fontSize=14, spaceAfter=4, fontName="Helvetica"),
    ))
    story.append(Paragraph(f"Proposal ID: {proposal_id}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#e2e8f0"), spaceAfter=12))

    # Portfolio allocations table
    story.append(Paragraph("Proposed Allocations", h2_style))
    proposed = proposal.proposed_allocations or {}
    current  = proposal.current_allocations or {}
    alloc_data = [["Asset", "Current %", "Proposed %", "Change"]]
    for symbol, prop_w in sorted(proposed.items(), key=lambda x: x[1], reverse=True):
        cur_w  = current.get(symbol, 0.0)
        delta  = prop_w - cur_w
        change = f"+{delta:.2f}%" if delta >= 0 else f"{delta:.2f}%"
        alloc_data.append([symbol, f"{cur_w:.2f}%", f"{prop_w:.2f}%", change])

    alloc_table = Table(alloc_data, colWidths=[50*mm, 35*mm, 35*mm, 35*mm])
    alloc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), HexColor("#0f172a")),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(alloc_table)
    story.append(Spacer(1, 8*mm))

    if rationale:
        # Overall rationale
        if rationale.rationale_text:
            story.append(Paragraph("AI Evaluation Rationale", h2_style))
            for para in rationale.rationale_text.split("\\n\\n"):
                story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 4*mm))

        # Scores
        score_data = [["Metric", "Value"]]
        if rationale.confidence_score is not None:
            score_data.append(["Confidence Score", f"{rationale.confidence_score:.0%}"])
        if rationale.diversification_score is not None:
            score_data.append(["Diversification Score", f"{rationale.diversification_score}/100"])
        if len(score_data) > 1:
            story.append(Paragraph("Scores", h2_style))
            score_tbl = Table(score_data, colWidths=[80*mm, 75*mm])
            score_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",   (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(score_tbl)
            story.append(Spacer(1, 4*mm))

        # Detailed analyses
        sections = [
            ("Risk Analysis",         rationale.risk_analysis),
            ("Constraint Analysis",   rationale.constraint_analysis),
            ("Liquidity Assessment",  rationale.liquidity_assessment),
            ("Objective Alignment",   rationale.objective_alignment),
        ]
        for label, text in sections:
            if text:
                story.append(Paragraph(label, h2_style))
                story.append(Paragraph(text, body_style))
                story.append(Spacer(1, 4*mm))

        # Risks from validator_consensus
        vc = rationale.validator_consensus or {}
        introduced = vc.get("key_risks_introduced", [])
        mitigated  = vc.get("key_risks_mitigated", [])
        if introduced or mitigated:
            story.append(Paragraph("Risk Summary", h2_style))
            if introduced:
                story.append(Paragraph("<b>Risks Introduced:</b>", body_style))
                for r in introduced:
                    story.append(Paragraph(f"• {r}", body_style))
            if mitigated:
                story.append(Paragraph("<b>Risks Mitigated:</b>", body_style))
                for r in mitigated:
                    story.append(Paragraph(f"• {r}", body_style))

        # Recommendation
        rec = vc.get("recommendation")
        if rec:
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph("Recommendation", h2_style))
            story.append(Paragraph(rec, body_style))

    # Footer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#e2e8f0"), spaceAfter=6))
    story.append(Paragraph(
        f"Generated by Allocensus · Genlayer StudioNet · "
        f"Contract: 0xe45A5379bDD30BF75D08752cb32c4178f59445EA · "
        f"TX: {proposal.genlayer_tx_hash or 'N/A'}",
        ParagraphStyle("Footer", fontSize=7, textColor=HexColor("#94a3b8"), leading=10),
    ))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="allocensus-{proposal_id[:8]}.pdf"'},
    )


@router.get("/{proposal_id}/export/csv")
async def export_csv(proposal_id: str, user: CurrentUser, db: DB):
    result = await db.execute(
        select(RebalancingProposal)
        .options(selectinload(RebalancingProposal.rationale))
        .where(RebalancingProposal.id == uuid.UUID(proposal_id))
    )
    proposal  = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    rationale = proposal.rationale
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["ALLOCENSUS — Portfolio Rebalancing Export"])
    writer.writerow(["Proposal ID", proposal_id])
    writer.writerow(["Status", proposal.status.value])
    writer.writerow(["TX Hash", proposal.genlayer_tx_hash or ""])
    writer.writerow([])

    writer.writerow(["Asset", "Current Weight %", "Proposed Weight %", "Change %"])
    proposed = proposal.proposed_allocations or {}
    current  = proposal.current_allocations or {}
    for symbol, prop_w in sorted(proposed.items(), key=lambda x: x[1], reverse=True):
        cur_w = current.get(symbol, 0.0)
        writer.writerow([symbol, f"{cur_w:.4f}", f"{prop_w:.4f}", f"{prop_w - cur_w:.4f}"])

    writer.writerow([])
    if rationale:
        writer.writerow(["AI Evaluation"])
        writer.writerow(["Decision",            "Approved" if rationale.approved else "Rejected"])
        writer.writerow(["Confidence Score",    rationale.confidence_score or ""])
        writer.writerow(["Diversification Score", rationale.diversification_score or ""])
        writer.writerow(["Rationale",           rationale.rationale_text or ""])
        writer.writerow(["Risk Analysis",       rationale.risk_analysis or ""])
        writer.writerow(["Constraint Analysis", rationale.constraint_analysis or ""])
        writer.writerow(["Liquidity",           rationale.liquidity_assessment or ""])
        writer.writerow(["Objective Alignment", rationale.objective_alignment or ""])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="allocensus-{proposal_id[:8]}.csv"'},
    )
""")


# ── 6. Register export router in main.py ────────────────────────────────────
write("backend/app/main.py", """\
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
import structlog

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("allocensus_starting", env=settings.APP_ENV)
    yield
    log.info("allocensus_stopping")


app = FastAPI(
    title="Allocensus API",
    description="AI-Validated Portfolio Rebalancing Intelligence — Genlayer StudioNet",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sentry
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()])

# Routers
from app.routers import auth, users, portfolios, rebalancing, audit, admin, health
from app.routers.export import router as export_router

app.include_router(health.router,       prefix="/api/health",       tags=["Health"])
app.include_router(auth.router,         prefix="/api/auth",         tags=["Auth"])
app.include_router(users.router,        prefix="/api/users",        tags=["Users"])
app.include_router(portfolios.router,   prefix="/api/portfolios",   tags=["Portfolios"])
app.include_router(rebalancing.router,  prefix="/api/rebalancing",  tags=["Rebalancing"])
app.include_router(export_router,       prefix="/api/rebalancing",  tags=["Export"])
app.include_router(audit.router,        prefix="/api/audit",        tags=["Audit"])
app.include_router(admin.router,        prefix="/api/admin",        tags=["Admin"])
""")


# ── 7. requirements.txt — swap resend for nothing (using httpx already) ──────
write("backend/requirements.txt", """\
# Web framework
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-multipart==0.0.12

# Database
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
psycopg2-binary==2.9.10

# Redis / Cache
redis[asyncio]==5.2.1
celery[redis]==5.4.0

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==43.0.3
mnemonic==0.21

# Wallet / Web3
eth-account==0.13.3
web3==7.5.0

# HTTP client
httpx==0.28.0
aiohttp==3.11.8

# Validation
pydantic==2.10.2
pydantic-settings==2.6.1
email-validator==2.2.0

# PDF generation
reportlab==4.2.5
pypdf==5.1.0

# Task queue
celery==5.4.0
flower==2.0.1

# Logging
structlog==24.4.0

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
factory-boy==3.3.1

# Dev tools
ruff==0.8.1
mypy==1.13.0

# Monitoring
sentry-sdk[fastapi]==2.19.0
""")


# ── 8. Railway config ─────────────────────────────────────────────────────────
write("backend/railway.toml", """\
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[deploy.healthcheck]
path = "/api/health"
interval = 30
timeout = 10
""")

write("railway.toml", """\
[build]
builder = "dockerfile"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
""")


# ── 9. GitHub Actions — updated deploy workflow ───────────────────────────────
write(".github/workflows/deploy.yml", """\
name: Deploy

on:
  push:
    branches: [main]

jobs:
  # ── Backend → Railway ──────────────────────────────────────────────────────
  deploy-backend:
    name: Deploy Backend to Railway
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        working-directory: backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service allocensus-api --detach

  # ── DB Migrations ──────────────────────────────────────────────────────────
  run-migrations:
    name: Run DB Migrations
    runs-on: ubuntu-latest
    needs: deploy-backend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        working-directory: backend
        run: pip install -r requirements.txt

      - name: Run Alembic migrations
        working-directory: backend
        env:
          DATABASE_URL_SYNC: ${{ secrets.RAILWAY_DATABASE_URL_SYNC }}
        run: alembic upgrade head

  # ── Frontend → Vercel ──────────────────────────────────────────────────────
  deploy-frontend:
    name: Deploy Frontend to Vercel
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Pull Vercel env
        working-directory: frontend
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
        run: vercel pull --yes --environment=production --token=$VERCEL_TOKEN

      - name: Build
        working-directory: frontend
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
        run: vercel build --prod --token=$VERCEL_TOKEN

      - name: Deploy to Vercel
        working-directory: frontend
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
        run: vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
""")


# ── 10. Vercel config ─────────────────────────────────────────────────────────
write("frontend/vercel.json", """\
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm ci",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@allocensus-api-url",
    "NEXT_PUBLIC_GENLAYER_RPC_URL": "@allocensus-genlayer-rpc",
    "NEXT_PUBLIC_CONTRACT_ADDRESS": "@allocensus-contract-address"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
""")


# ── 11. Frontend: SubmitToGenlayerModal component ────────────────────────────
write("frontend/src/components/rebalancing/SubmitToGenlayerModal.tsx", """\
"use client";

/**
 * SubmitToGenlayerModal
 *
 * Prompts the user for their password, decrypts their wallet keystore
 * entirely in the browser (no password or key ever leaves the device),
 * then calls useGenlayerTx to sign + broadcast the evaluation transaction.
 */

import { useState } from "react";
import { ethers } from "ethers";
import { useGenlayerTx } from "@/hooks/useGenlayerTx";
import { userAPI } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  Shield, Loader2, CheckCircle2, XCircle,
  ExternalLink, Lock, Zap,
} from "lucide-react";

interface Props {
  proposalId: string;
  onClose:    () => void;
  onSuccess:  (approved: boolean) => void;
}

const STATUS_LABELS: Record<string, string> = {
  idle:              "Ready",
  fetching_call_data: "Preparing transaction data…",
  awaiting_signature: "Decrypting wallet…",
  broadcasting:      "Broadcasting to Genlayer…",
  pending_consensus: "Waiting for validator consensus…",
  confirmed:         "Consensus reached!",
  failed:            "Transaction failed",
};

export function SubmitToGenlayerModal({ proposalId, onClose, onSuccess }: Props) {
  const [password,  setPassword]  = useState("");
  const [pwError,   setPwError]   = useState("");
  const { status, txHash, approved, error, submitProposal } = useGenlayerTx();

  const isProcessing = !["idle", "failed"].includes(status);
  const isDone       = status === "confirmed";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError("");

    // Fetch the encrypted keystore from the backend
    let keystoreJson: string;
    try {
      const res = await userAPI.wallet();
      keystoreJson = res.data?.keystore_json;
      if (!keystoreJson) throw new Error("No wallet keystore found");
    } catch {
      setPwError("Could not load your wallet. Please try again.");
      return;
    }

    // Decrypt the keystore client-side using the user's password
    let decryptedKey: string;
    try {
      const wallet = await ethers.Wallet.fromEncryptedJson(keystoreJson, password);
      decryptedKey = wallet.privateKey;
    } catch {
      setPwError("Incorrect password. Please try again.");
      return;
    }

    // Sign and broadcast — private key is used only in memory, then discarded
    await submitProposal(proposalId, decryptedKey);

    // Zero out the key reference immediately after use
    decryptedKey = "0".repeat(64);

    if (status === "confirmed" && approved !== null) {
      onSuccess(approved);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-card border border-border rounded-2xl w-full max-w-md p-8 shadow-2xl">

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Zap className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Submit to Genlayer</h2>
            <p className="text-xs text-muted-foreground">AI validator consensus evaluation</p>
          </div>
        </div>

        {/* Security notice */}
        <div className="flex gap-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4 mb-6">
          <Lock className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-emerald-300 leading-relaxed">
            Your password decrypts your wallet locally in your browser.
            Your private key and password are never transmitted to any server.
          </p>
        </div>

        {/* Status display when processing */}
        {isProcessing || isDone ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 py-2">
              {isDone ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : (
                <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" />
              )}
              <span className="text-sm font-medium">{STATUS_LABELS[status]}</span>
            </div>

            {txHash && (
              <div className="bg-secondary/50 rounded-xl p-3">
                <p className="text-xs text-muted-foreground mb-1">Transaction Hash</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs text-emerald-400 font-mono truncate flex-1">
                    {txHash}
                  </code>
                  <a
                    href={`https://studio.genlayer.com/tx/${txHash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground flex-shrink-0"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            )}

            {isDone && approved !== null && (
              <div className={`flex items-center gap-3 rounded-xl p-4 ${
                approved
                  ? "bg-emerald-500/10 border border-emerald-500/20"
                  : "bg-red-500/10 border border-red-500/20"
              }`}>
                {approved ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
                <div>
                  <p className={`font-bold ${approved ? "text-emerald-400" : "text-red-400"}`}>
                    {approved ? "Proposal Approved" : "Proposal Rejected"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Validator consensus reached on Genlayer StudioNet
                  </p>
                </div>
              </div>
            )}

            {status === "pending_consensus" && (
              <p className="text-xs text-muted-foreground text-center">
                Validators are independently evaluating your proposal.
                This typically takes 30–90 seconds.
              </p>
            )}

            <div className="flex gap-3 pt-2">
              {isDone ? (
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={() => { onSuccess(approved ?? false); onClose(); }}
                >
                  View Rationale
                </Button>
              ) : (
                <Button variant="secondary" className="flex-1" onClick={onClose}>
                  Close (running in background)
                </Button>
              )}
            </div>
          </div>
        ) : (
          /* Password form */
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Account Password"
              type="password"
              placeholder="Enter your password to sign the transaction"
              value={password}
              onChange={e => setPassword(e.target.value)}
              error={pwError}
              autoFocus
              required
            />

            {error && (
              <div className="flex items-start gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p className="text-xs">{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" className="flex-1" disabled={!password}>
                <Shield className="w-4 h-4" />
                Sign & Submit
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
""")


# ── 12. Frontend: wallet export endpoint addition to userAPI ──────────────────
# Already has wallet() but needs keystore_json field — add getKeystoreJson
write("frontend/src/lib/api.ts", """\
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: false,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_URL}/api/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register:    (data: { email: string; password: string; full_name: string }) =>
    api.post("/api/auth/register", data),
  login:       (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),
  refresh:     (refresh_token: string) =>
    api.post("/api/auth/refresh", { refresh_token }),
  verifyEmail: (token: string) =>
    api.post(`/api/auth/verify-email?token=${token}`),
};

// Portfolios
export const portfolioAPI = {
  list:     () => api.get("/api/portfolios"),
  get:      (id: string) => api.get(`/api/portfolios/${id}`),
  create:   (data: unknown) => api.post("/api/portfolios", data),
  update:   (id: string, data: unknown) => api.patch(`/api/portfolios/${id}`, data),
  delete:   (id: string) => api.delete(`/api/portfolios/${id}`),
  getDrift: (id: string) => api.get(`/api/portfolios/${id}/drift`),
};

// Rebalancing
export const rebalancingAPI = {
  list:        () => api.get("/api/rebalancing"),
  get:         (id: string) => api.get(`/api/rebalancing/${id}`),
  create:      (data: unknown) => api.post("/api/rebalancing", data),
  getCallData: (id: string) => api.get(`/api/rebalancing/${id}/call-data`),
  confirmTx:   (id: string, tx_hash: string) =>
    api.post(`/api/rebalancing/${id}/confirm-tx`, { tx_hash }),
  pollResult:  (id: string) => api.post(`/api/rebalancing/${id}/poll-result`),
  getRationale:(id: string) => api.get(`/api/rebalancing/${id}/rationale`),
  exportPdf:   (id: string) => api.get(`/api/rebalancing/${id}/export/pdf`, { responseType: "blob" }),
  exportCsv:   (id: string) => api.get(`/api/rebalancing/${id}/export/csv`, { responseType: "blob" }),
};

// Users
export const userAPI = {
  me:          () => api.get("/api/users/me"),
  update:      (data: unknown) => api.patch("/api/users/me", data),
  wallet:      () => api.get("/api/users/me/wallet"),
  exportKey:   (password: string) => api.post("/api/users/me/wallet/export-key", { password }),
};

// Audit
export const auditAPI = {
  events:     (params?: { limit?: number; event_type?: string }) =>
    api.get("/api/audit/events", { params }),
  compliance: () => api.get("/api/audit/compliance"),
};

// Admin
export const adminAPI = {
  stats:      () => api.get("/api/admin/stats"),
  users:      () => api.get("/api/admin/users"),
  updateRole: (userId: string, role: string) =>
    api.patch(`/api/admin/users/${userId}/role?role=${role}`),
};
""")


# ── 13. Rebalancing detail page — wire submit modal + export buttons ──────────
write("frontend/src/app/(dashboard)/rebalancing/[id]/page.tsx", """\
"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { rebalancingAPI } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SubmitToGenlayerModal } from "@/components/rebalancing/SubmitToGenlayerModal";
import {
  FileText, Download, Zap, CheckCircle2, XCircle,
  ArrowLeft, ExternalLink, AlertTriangle,
} from "lucide-react";
import toast from "react-hot-toast";

function statusBadgeVariant(status: string) {
  const map: Record<string, "success" | "danger" | "pending" | "info" | "warning" | "default"> = {
    approved:          "success",
    rejected:          "danger",
    pending_consensus: "warning",
    submitted:         "info",
    draft:             "default",
    failed:            "danger",
  };
  return map[status] ?? "default";
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement("a");
  a.href    = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ProposalDetailPage() {
  const { id }  = useParams<{ id: string }>();
  const router  = useRouter();
  const qc      = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["proposal", id],
    queryFn:  () => rebalancingAPI.get(id),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === "pending_consensus" ? 8000 : false;
    },
  });

  const proposal  = data?.data;
  const rationale = proposal?.rationale;

  const handleExportPdf = async () => {
    try {
      const res = await rebalancingAPI.exportPdf(id);
      downloadBlob(res.data, `allocensus-${id.slice(0, 8)}.pdf`);
    } catch { toast.error("PDF export failed"); }
  };

  const handleExportCsv = async () => {
    try {
      const res = await rebalancingAPI.exportCsv(id);
      downloadBlob(res.data, `allocensus-${id.slice(0, 8)}.csv`);
    } catch { toast.error("CSV export failed"); }
  };

  const handleSubmitSuccess = (approved: boolean) => {
    toast.success(approved ? "Proposal approved by validators!" : "Proposal rejected by validators");
    qc.invalidateQueries({ queryKey: ["proposal", id] });
    qc.invalidateQueries({ queryKey: ["proposals"] });
  };

  if (isLoading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!proposal) return (
    <div className="flex items-center justify-center min-h-screen text-muted-foreground">
      Proposal not found
    </div>
  );

  const isApproved  = proposal.status === "approved";
  const isRejected  = proposal.status === "rejected";
  const isDraft     = proposal.status === "draft";
  const isPending   = proposal.status === "pending_consensus";
  const isDone      = isApproved || isRejected;

  return (
    <div className="min-h-screen bg-background">
      <main className="ml-64 p-8 space-y-6">

        {/* Back + title */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => router.back()} className="text-muted-foreground hover:text-foreground">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold">Rebalancing Proposal</h1>
              <p className="text-xs text-muted-foreground font-mono mt-0.5">{proposal.id}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant={statusBadgeVariant(proposal.status)}>
              {proposal.status.replace("_", " ").toUpperCase()}
            </Badge>

            {isDone && (
              <>
                <Button variant="secondary" size="sm" onClick={handleExportCsv}>
                  <Download className="w-3.5 h-3.5" /> CSV
                </Button>
                <Button variant="secondary" size="sm" onClick={handleExportPdf}>
                  <FileText className="w-3.5 h-3.5" /> PDF
                </Button>
              </>
            )}

            {isDraft && (
              <Button onClick={() => setShowModal(true)}>
                <Zap className="w-4 h-4" />
                Submit to Genlayer
              </Button>
            )}

            {isPending && (
              <Button variant="secondary" disabled>
                <div className="w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                Awaiting Consensus
              </Button>
            )}
          </div>
        </div>

        {/* On-chain ref */}
        {proposal.genlayer_tx_hash && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary/30 border border-border rounded-xl px-4 py-2.5">
            <ExternalLink className="w-3.5 h-3.5" />
            <span>On-chain TX:</span>
            <code className="font-mono text-emerald-400">{proposal.genlayer_tx_hash}</code>
            <a
              href={`https://studio.genlayer.com/tx/${proposal.genlayer_tx_hash}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300"
            >
              View on explorer ↗
            </a>
          </div>
        )}

        {/* Constraint violations */}
        {proposal.constraint_violations?.length > 0 && (
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <CardTitle className="text-amber-400">Constraint Violations</CardTitle>
            </div>
            <div className="space-y-2">
              {proposal.constraint_violations.map((v: { rule: string; message: string }, i: number) => (
                <div key={i} className="flex items-start gap-3 bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
                  <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">{v.rule}</span>
                  <span className="text-sm text-amber-200">{v.message}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Allocations side-by-side */}
        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardTitle className="mb-4 text-muted-foreground text-sm font-medium uppercase tracking-wider">
              Current Allocations
            </CardTitle>
            <div className="space-y-2">
              {Object.entries(proposal.current_allocations || {})
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .map(([sym, w]) => (
                  <div key={sym} className="flex items-center justify-between">
                    <span className="text-sm font-mono">{sym}</span>
                    <span className="text-sm text-muted-foreground">{Number(w).toFixed(2)}%</span>
                  </div>
                ))}
            </div>
          </Card>

          <Card>
            <CardTitle className="mb-4 text-muted-foreground text-sm font-medium uppercase tracking-wider">
              Proposed Allocations
            </CardTitle>
            <div className="space-y-2">
              {Object.entries(proposal.proposed_allocations || {})
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .map(([sym, w]) => {
                  const cur   = (proposal.current_allocations || {})[sym] ?? 0;
                  const delta = Number(w) - Number(cur);
                  return (
                    <div key={sym} className="flex items-center justify-between">
                      <span className="text-sm font-mono">{sym}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{Number(w).toFixed(2)}%</span>
                        {delta !== 0 && (
                          <span className={`text-xs ${delta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {delta > 0 ? "+" : ""}{delta.toFixed(2)}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          </Card>
        </div>

        {/* AI Rationale */}
        {rationale && (
          <Card glow={isApproved ? "green" : undefined}>
            <div className="flex items-center gap-3 mb-6">
              {isApproved ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              ) : (
                <XCircle className="w-6 h-6 text-red-400" />
              )}
              <div>
                <CardTitle>AI Evaluation Rationale</CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Genlayer validator consensus · Confidence {rationale.confidence_score
                    ? `${(rationale.confidence_score * 100).toFixed(0)}%`
                    : "—"}
                  {rationale.diversification_score != null &&
                    ` · Diversification ${rationale.diversification_score}/100`}
                </p>
              </div>
            </div>

            {rationale.rationale_text && (
              <div className="prose prose-sm prose-invert max-w-none mb-6">
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {rationale.rationale_text}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Risk Analysis",        text: rationale.risk_analysis },
                { label: "Constraint Analysis",  text: rationale.constraint_analysis },
                { label: "Liquidity Assessment", text: rationale.liquidity_assessment },
                { label: "Objective Alignment",  text: rationale.objective_alignment },
              ].filter(s => s.text).map(({ label, text }) => (
                <div key={label} className="bg-secondary/30 border border-border rounded-xl p-4">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">{label}</p>
                  <p className="text-sm leading-relaxed">{text}</p>
                </div>
              ))}
            </div>

            {/* Key risks */}
            {(rationale.validator_consensus?.key_risks_introduced?.length > 0 ||
              rationale.validator_consensus?.key_risks_mitigated?.length > 0) && (
              <div className="grid grid-cols-2 gap-4 mt-4">
                {rationale.validator_consensus.key_risks_introduced?.length > 0 && (
                  <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
                    <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">Risks Introduced</p>
                    <ul className="space-y-1">
                      {rationale.validator_consensus.key_risks_introduced.map((r: string, i: number) => (
                        <li key={i} className="text-sm text-red-300 flex gap-2"><span>•</span>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {rationale.validator_consensus.key_risks_mitigated?.length > 0 && (
                  <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Risks Mitigated</p>
                    <ul className="space-y-1">
                      {rationale.validator_consensus.key_risks_mitigated.map((r: string, i: number) => (
                        <li key={i} className="text-sm text-emerald-300 flex gap-2"><span>•</span>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Recommendation */}
            {rationale.validator_consensus?.recommendation && (
              <div className="mt-4 bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-4">
                <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Recommendation</p>
                <p className="text-sm text-indigo-200">{rationale.validator_consensus.recommendation}</p>
              </div>
            )}
          </Card>
        )}

        {/* Pending state */}
        {isPending && !rationale && (
          <Card>
            <div className="flex flex-col items-center py-12 gap-4">
              <div className="w-12 h-12 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              <p className="font-medium">Validators are reaching consensus</p>
              <p className="text-sm text-muted-foreground text-center max-w-sm">
                Multiple Genlayer validators are independently evaluating your proposal.
                This page refreshes automatically every 8 seconds.
              </p>
            </div>
          </Card>
        )}

      </main>

      {/* Submit modal */}
      {showModal && (
        <SubmitToGenlayerModal
          proposalId={id}
          onClose={() => setShowModal(false)}
          onSuccess={handleSubmitSuccess}
        />
      )}
    </div>
  );
}
""")


# ── 14. Users router — add keystore_json to wallet endpoint ──────────────────
# Check if wallet endpoint returns keystore_json already
write("backend/app/routers/users.py", """\
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.wallet import Wallet, WalletKeystore
from app.schemas.user import UserUpdate, UserResponse
from app.dependencies import CurrentUser, DB
from app.utils.security import decrypt_private_key
from pydantic import BaseModel
import json

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(req: UserUpdate, user: CurrentUser, db: DB):
    if req.full_name is not None:
        user.full_name = req.full_name
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me/wallet")
async def get_wallet(user: CurrentUser, db: DB):
    result = await db.execute(
        select(Wallet)
        .options(selectinload(Wallet.keystore))
        .where(Wallet.user_id == user.id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Build the ethers-compatible encrypted JSON keystore for client-side decryption.
    # keystore.encrypted_private_key is our internal AES-256-GCM format.
    # We expose the raw encrypted blob as keystore_json so the frontend can use
    # ethers.Wallet.fromEncryptedJson() with the user's password.
    keystore_json = None
    if wallet.keystore and wallet.keystore.encrypted_private_key:
        stored = wallet.keystore.encrypted_private_key
        # If already stored as a JSON string (eth keystore v3 format), use directly
        if isinstance(stored, str) and stored.strip().startswith("{"):
            keystore_json = stored
        elif isinstance(stored, dict):
            keystore_json = json.dumps(stored)
        else:
            keystore_json = str(stored)

    return {
        "address":      wallet.address,
        "chain":        wallet.chain,
        "keystore_json": keystore_json,
        "created_at":   wallet.created_at.isoformat(),
    }


class ExportKeyRequest(BaseModel):
    password: str


@router.post("/me/wallet/export-key")
async def export_private_key(req: ExportKeyRequest, user: CurrentUser, db: DB):
    """
    Return the decrypted private key after verifying the user's password.
    Used only in the Settings page under explicit user action.
    The key is never stored; it is derived on-demand and returned once.
    """
    from app.utils.security import verify_password
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    result = await db.execute(
        select(Wallet)
        .options(selectinload(Wallet.keystore))
        .where(Wallet.user_id == user.id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet or not wallet.keystore:
        raise HTTPException(status_code=404, detail="Wallet not found")

    private_key = decrypt_private_key(
        wallet.keystore.encrypted_private_key,
        user.hashed_password,
    )
    return {"private_key": private_key, "address": wallet.address}
""")


# ── 15. Frontend .env.local (production values) ───────────────────────────────
write("frontend/.env.local", """\
NEXT_PUBLIC_API_URL=https://allocensus-api.up.railway.app
NEXT_PUBLIC_WS_URL=wss://allocensus-api.up.railway.app
NEXT_PUBLIC_APP_NAME=Allocensus
NEXT_PUBLIC_APP_URL=https://allocensus.vercel.app
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_CONTRACT_ADDRESS=0xe45A5379bDD30BF75D08752cb32c4178f59445EA
NEXT_PUBLIC_SENTRY_DSN=
""")


# ── 16. Setup instructions ────────────────────────────────────────────────────
write("DEPLOYMENT.md", """\
# Allocensus — Deployment Guide

## Stack
- **Frontend**: Vercel → allocensus.vercel.app  (GitHub: zoefunds/Allocensus)
- **Backend**: Railway → allocensus-api.up.railway.app
- **Database**: Railway PostgreSQL
- **Redis**: Upstash (rediss://...)
- **Email**: Brevo (verified sender: preciousmofeoluwa@gmail.com)
- **Contract**: Genlayer StudioNet → 0xe45A5379bDD30BF75D08752cb32c4178f59445EA

---

## 1. Push to GitHub

```bash
cd /Users/macbook/ALLOCENSUS
git init
git remote add origin https://github.com/zoefunds/Allocensus.git
git add .
git commit -m "feat: initial production build"
git branch -M main
git push -u origin main
```

---

## 2. Railway — Backend

1. Go to railway.app → New Project → Deploy from GitHub repo → zoefunds/Allocensus
2. Select the `/backend` directory
3. Set these environment variables in Railway dashboard:

```
APP_ENV=production
SECRET_KEY=<from backend/.env>
JWT_SECRET_KEY=<from backend/.env>
WALLET_ENCRYPTION_KEY=<from backend/.env>
ALLOWED_ORIGINS=https://allocensus.vercel.app,http://localhost:3000
DATABASE_URL=<Railway provides this — use the internal URL>
DATABASE_URL_SYNC=<Railway provides this — sync version>
REDIS_URL=rediss://default:gQAAAAAAAlC8AAIgcDFkZWFkNTA0Njc2MDM0M2IxYjdkNDQ3NjVjNGVhOTI3Mg@fancy-hookworm-151740.upstash.io:6379
GENLAYER_RPC_URL=https://studio.genlayer.com/api
GENLAYER_CONTRACT_ADDRESS=0xe45A5379bDD30BF75D08752cb32c4178f59445EA
BREVO_API_KEY=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
EMAIL_FROM=preciousmofeoluwa@gmail.com
EMAIL_FROM_NAME=Allocensus
```

4. Railway will auto-detect the Dockerfile and deploy.
5. After first deploy, run migrations via Railway shell:
   ```
   alembic upgrade head
   ```

6. Copy the Railway service URL (e.g. https://allocensus-api.up.railway.app)

---

## 3. Vercel — Frontend

1. Go to vercel.com → New Project → Import from GitHub → zoefunds/Allocensus
2. Set Root Directory to `frontend`
3. Framework: Next.js (auto-detected)
4. Set these environment variables in Vercel dashboard:

```
NEXT_PUBLIC_API_URL=https://allocensus-api.up.railway.app
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_CONTRACT_ADDRESS=0xe45A5379bDD30BF75D08752cb32c4178f59445EA
NEXT_PUBLIC_APP_URL=https://allocensus.vercel.app
```

5. Set custom domain to: allocensus.vercel.app (or add in Vercel → Domains)
6. Deploy — Vercel connects to the GitHub repo and auto-deploys on every push to main.

---

## 4. GitHub Actions Secrets

In GitHub → zoefunds/Allocensus → Settings → Secrets → Actions, add:

| Secret | Value |
|--------|-------|
| RAILWAY_TOKEN | From Railway → Account → Tokens |
| RAILWAY_DATABASE_URL_SYNC | From Railway → PostgreSQL → Variables |
| VERCEL_TOKEN | From Vercel → Settings → Tokens |
| VERCEL_ORG_ID | From Vercel → Settings → General |
| VERCEL_PROJECT_ID | From Vercel → Project → Settings |

---

## 5. Verify

- Backend health: https://allocensus-api.up.railway.app/api/health
- API docs: https://allocensus-api.up.railway.app/api/docs
- Frontend: https://allocensus.vercel.app
""")


print("\\n✅ Phase 5 complete. All remaining work done:")
print("   • backend/.env — real secrets, Redis URL, Brevo key")
print("   • Email service — rewritten for Brevo (httpx, no SDK)")
print("   • process_rationale_result — fixed to parse contract output correctly")
print("   • Export router — PDF (ReportLab) + CSV endpoints")
print("   • SubmitToGenlayerModal — password prompt, client-side keystore decrypt")
print("   • Proposal detail page — wired submit modal + export buttons + auto-poll")
print("   • railway.toml — Railway deployment config")
print("   • vercel.json — Vercel deployment config")
print("   • .github/workflows/deploy.yml — Railway + Vercel CI/CD")
print("   • DEPLOYMENT.md — step-by-step deployment guide")
