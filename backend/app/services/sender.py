from __future__ import annotations

import datetime as dt
import hashlib
import smtplib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Client, Delivery, Greeting
from app.services.email_rendering import build_smtp_message


def _idempotency_key(*, greeting_id: int, channel: str, recipient: str) -> str:
    raw = f"{greeting_id}:{channel}:{recipient}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:40]


async def send_greeting_file(
    session: AsyncSession,
    *,
    greeting: Greeting,
    recipient: str,
    outbox_dir: str | Path | None = None,
) -> Delivery:
    """MVP sender: writes a .txt message into outbox directory.

    Idempotent by (greeting_id, channel, recipient).
    """
    channel = "file"
    out_dir = Path(outbox_dir or settings.outbox_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    key = _idempotency_key(greeting_id=greeting.id, channel=channel, recipient=recipient)
    existing = (
        await session.execute(select(Delivery).where(Delivery.idempotency_key == key))
    ).scalar_one_or_none()
    if existing:
        return existing

    filename = f"delivery_{greeting.id}_{key}.txt"
    path = out_dir / filename
    payload = "\n".join(
        [
            f"TO: {recipient}",
            f"SUBJECT: {greeting.subject}",
            "",
            greeting.body,
            "",
            f"IMAGE: {greeting.image_path or ''}",
        ]
    )
    path.write_text(payload, encoding="utf-8")

    delivery = Delivery(
        greeting_id=greeting.id,
        channel=channel,
        recipient=recipient,
        status="sent",
        provider_message=f"written:{path.name}",
        sent_at=dt.datetime.now(dt.timezone.utc),
        idempotency_key=key,
    )
    session.add(delivery)
    await session.commit()
    return delivery


def _split_domains(csv: str) -> set[str]:
    return {d.strip().lower() for d in (csv or "").split(",") if d.strip()}


def _is_demo_or_test_email(email: str) -> bool:
    low = (email or "").strip().lower()
    if not low:
        return True
    if low.endswith("@example.com"):
        return True
    if low.startswith("demo_client_") and low.endswith("@example.com"):
        return True
    # common non-routable examples
    if low.endswith(".invalid") or low.endswith(".example"):
        return True
    return False


def _recipient_domain(email: str) -> str:
    low = (email or "").strip().lower()
    if "@" not in low:
        return ""
    return low.split("@", 1)[1]


async def send_greeting(
    session: AsyncSession,
    *,
    greeting: Greeting,
    recipient: str,
    client: Client | None = None,
) -> Delivery:
    """Send greeting using configured SEND_MODE with safety guards.

    - Demo clients (Client.is_demo) are NEVER sent via SMTP.
    - *@example.com (and other test-ish domains) are blocked by default.
    - Optional domain allowlist for SMTP.
    """
    mode = (settings.send_mode or "file").lower()

    # Resolve client if needed (for safety rules and for demo fallbacks).
    if client is None and greeting.client_id is not None:
        client = (
            await session.execute(select(Client).where(Client.id == greeting.client_id))
        ).scalar_one_or_none()

    # Safety UX: if SMTP is enabled, NEVER send real emails to demo clients, but still
    # allow the demo flow to be shown by writing to file outbox instead.
    effective_mode = mode
    if effective_mode == "smtp" and client is not None and bool(getattr(client, "is_demo", False)):
        effective_mode = "file"

    # Determine channel (MVP: only email + file)
    channel = "email" if effective_mode == "smtp" else "file"

    key = _idempotency_key(greeting_id=greeting.id, channel=channel, recipient=recipient)
    existing = (
        await session.execute(select(Delivery).where(Delivery.idempotency_key == key))
    ).scalar_one_or_none()
    if existing:
        return existing

    if effective_mode == "noop":
        d = Delivery(
            greeting_id=greeting.id,
            channel=channel,
            recipient=recipient,
            status="skipped",
            provider_message="noop",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d

    if effective_mode == "file":
        return await send_greeting_file(session, greeting=greeting, recipient=recipient)

    if effective_mode != "smtp":
        # Unknown mode -> safe fallback to file
        return await send_greeting_file(session, greeting=greeting, recipient=recipient)

    # SMTP mode: safety checks
    # Require a valid email recipient for SMTP.
    if "@" not in (recipient or ""):
        d = Delivery(
            greeting_id=greeting.id,
            channel="email",
            recipient=recipient,
            status="error",
            provider_message="smtp:invalid-email-recipient",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d

    if client is not None and bool(getattr(client, "is_demo", False)):
        d = Delivery(
            greeting_id=greeting.id,
            channel="email",
            recipient=recipient,
            status="skipped",
            provider_message="blocked:demo-client",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d

    if _is_demo_or_test_email(recipient):
        d = Delivery(
            greeting_id=greeting.id,
            channel="email",
            recipient=recipient,
            status="skipped",
            provider_message="blocked:test-recipient",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d

    # Domain allowlist (recommended): for safety, by default we require allowlist OR explicit allow-all flag.
    allowlist = _split_domains(settings.smtp_allowlist_domains)
    if not settings.smtp_allow_all_recipients:
        dom = _recipient_domain(recipient)
        if not allowlist:
            d = Delivery(
                greeting_id=greeting.id,
                channel="email",
                recipient=recipient,
                status="skipped",
                provider_message="blocked:allowlist-empty",
                sent_at=dt.datetime.now(dt.timezone.utc),
                idempotency_key=key,
            )
            session.add(d)
            await session.commit()
            return d
        if dom not in allowlist:
            d = Delivery(
                greeting_id=greeting.id,
                channel="email",
                recipient=recipient,
                status="skipped",
                provider_message=f"blocked:domain-not-allowlisted:{dom}",
                sent_at=dt.datetime.now(dt.timezone.utc),
                idempotency_key=key,
            )
            session.add(d)
            await session.commit()
            return d

    # SMTP config
    if not settings.smtp_host:
        d = Delivery(
            greeting_id=greeting.id,
            channel="email",
            recipient=recipient,
            status="error",
            provider_message="smtp:not-configured",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d

    from_email = settings.smtp_from_email or settings.smtp_username or "no-reply@example.com"
    msg = build_smtp_message(greeting=greeting, recipient=recipient, from_email=from_email)

    try:
        if settings.smtp_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                int(settings.smtp_port),
                timeout=float(settings.smtp_timeout_sec),
            ) as s:
                if settings.smtp_username and settings.smtp_password:
                    s.login(settings.smtp_username, settings.smtp_password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(
                settings.smtp_host,
                int(settings.smtp_port),
                timeout=float(settings.smtp_timeout_sec),
            ) as s:
                if settings.smtp_starttls:
                    s.starttls()
                if settings.smtp_username and settings.smtp_password:
                    s.login(settings.smtp_username, settings.smtp_password)
                s.send_message(msg)
        d = Delivery(
            greeting_id=greeting.id,
            channel="email",
            recipient=recipient,
            status="sent",
            provider_message="smtp:sent",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d
    except Exception as e:
        d = Delivery(
            greeting_id=greeting.id,
            channel="email",
            recipient=recipient,
            status="error",
            provider_message=f"smtp:error:{e.__class__.__name__}",
            sent_at=dt.datetime.now(dt.timezone.utc),
            idempotency_key=key,
        )
        session.add(d)
        await session.commit()
        return d
