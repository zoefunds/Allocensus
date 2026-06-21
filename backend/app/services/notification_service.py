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


def _base_html(body: str) -> str:
    return (
        '<!DOCTYPE html><html><body style="font-family:sans-serif;background:#0a0f1e;'
        'color:#e2e8f0;padding:40px;">'
        '<div style="max-width:520px;margin:auto;background:#0f1629;border:1px solid'
        ' #1e2d4a;border-radius:16px;padding:40px;">'
        '<div style="margin-bottom:24px;">'
        '<span style="background:#10b981;color:#fff;font-size:12px;font-weight:700;'
        'padding:4px 12px;border-radius:20px;letter-spacing:1px;">ALLOCENSUS</span>'
        "</div>"
        + body
        + "</div></body></html>"
    )


def _btn(url: str, label: str) -> str:
    return (
        '<a href="' + url + '" style="display:inline-block;background:#10b981;color:#fff;'
        'font-weight:600;font-size:14px;padding:14px 28px;border-radius:10px;'
        'text-decoration:none;">' + label + "</a>"
    )


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
    verify_url = APP_URL + "/verify-email?token=" + token
    body = (
        '<h1 style="font-size:24px;font-weight:700;color:#f8fafc;margin:0 0 16px;">'
        "Verify your email</h1>"
        '<p style="color:#94a3b8;line-height:1.6;margin:0 0 32px;">'
        "Welcome to Allocensus. Click below to verify your email and activate your account "
        "along with your auto-provisioned BIP-39 HD wallet.</p>"
        + _btn(verify_url, "Verify Email Address")
        + '<p style="color:#475569;font-size:12px;margin:32px 0 0;">This link expires in 24 hours.</p>'
    )
    await _send("Verify your Allocensus account", email, _base_html(body))


async def send_welcome_email(email: str, full_name: str, wallet_address: str) -> None:
    body = (
        '<h1 style="font-size:24px;font-weight:700;color:#f8fafc;margin:0 0 16px;">'
        "Welcome, " + full_name + "</h1>"
        '<p style="color:#94a3b8;line-height:1.6;margin:0 0 24px;">'
        "Your Allocensus account is active. A BIP-39 HD wallet has been automatically "
        "provisioned and is ready to sign Genlayer transactions.</p>"
        '<div style="background:#0d1a2e;border:1px solid #1e2d4a;border-radius:10px;'
        'padding:16px;margin:0 0 28px;">'
        '<p style="color:#64748b;font-size:11px;font-weight:600;letter-spacing:1px;margin:0 0 6px;">'
        "WALLET ADDRESS</p>"
        '<code style="color:#10b981;font-size:13px;word-break:break-all;">' + wallet_address + "</code>"
        "</div>"
        + _btn(APP_URL + "/dashboard", "Open Dashboard")
    )
    await _send("Welcome to Allocensus", email, _base_html(body))


async def send_rationale_ready_email(email: str, proposal_id: str, approved: bool) -> None:
    status_word = "APPROVED" if approved else "REJECTED"
    color       = "#10b981" if approved else "#ef4444"
    bg_color    = "#0d2015" if approved else "#200d0d"
    detail_url  = APP_URL + "/rebalancing/" + proposal_id
    body = (
        '<h1 style="font-size:24px;font-weight:700;color:#f8fafc;margin:0 0 16px;">'
        "Evaluation Complete</h1>"
        '<div style="background:' + bg_color + ';border:1px solid ' + color + '33;'
        'border-radius:12px;padding:20px;margin:0 0 24px;">'
        '<p style="font-size:28px;font-weight:800;color:' + color + ';margin:0 0 4px;">'
        + status_word + "</p>"
        '<p style="color:#94a3b8;font-size:14px;margin:0;">'
        "Genlayer validator consensus has been reached on your rebalancing proposal.</p>"
        "</div>"
        '<p style="color:#94a3b8;line-height:1.6;margin:0 0 28px;">'
        "View the full AI rationale and on-chain audit trail in your dashboard.</p>"
        + _btn(detail_url, "View Full Rationale")
        + '<p style="color:#475569;font-size:12px;margin:32px 0 0;">Proposal ID: ' + proposal_id + "</p>"
    )
    await _send("Rebalancing Proposal " + status_word + " — Allocensus", email, _base_html(body))
