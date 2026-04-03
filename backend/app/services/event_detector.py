from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Client, Event, Holiday
from app.services.dates import daterange_inclusive, next_occurrence
from app.services.holiday_catalog import (
    general_holidays_in_window,
    professional_holidays_for_client,
)


async def ensure_upcoming_events(
    session: AsyncSession,
    *,
    today: dt.date,
    lookahead_days: int,
    max_holiday_recipients: int | None = None,
) -> int:
    """Create missing Events in DB for upcoming birthdays and holidays.

    Idempotency is achieved by unique constraint on events.
    Returns number of newly created events (best-effort).
    """

    end = today + dt.timedelta(days=lookahead_days)
    window_days = daterange_inclusive(today, end)

    created = 0
    max_holiday_recipients = (
        int(max_holiday_recipients)
        if max_holiday_recipients is not None
        else int(settings.max_holiday_recipients)
    )

    # Birthdays (per client)
    client_rows = (
        await session.execute(select(Client.id, Client.birth_date, Client.profession))
    ).all()
    client_ids: list[int] = []
    prof_by_client: dict[int, str] = {}
    for client_id, birth_date, profession in client_rows:
        client_ids.append(client_id)
        if profession:
            prof_by_client[int(client_id)] = str(profession)
        if not birth_date:
            continue
        occ = next_occurrence(birth_date.month, birth_date.day, today=today)
        if occ not in window_days:
            continue
        title = "День рождения"
        ev = Event(
            client_id=client_id,
            event_type="birthday",
            event_date=occ,
            title=title,
            details={},
        )
        session.add(ev)
        try:
            await session.commit()
            created += 1
        except IntegrityError:
            await session.rollback()

    # Holidays (global → per client for MVP)
    holiday_rows = (
        await session.execute(
            select(Holiday.date, Holiday.title, Holiday.tags)
            .where(Holiday.date >= today)
            .where(Holiday.date <= end)
        )
    ).all()
    for h_date, h_title, h_tags in holiday_rows:
        for client_id in client_ids[:max_holiday_recipients]:
            title = h_title
            ev = Event(
                client_id=client_id,
                event_type="holiday",
                event_date=h_date,
                title=title,
                details={"holiday_tags": h_tags},
            )
            session.add(ev)
            try:
                await session.commit()
                created += 1
            except IntegrityError:
                await session.rollback()

    # Built-in recurring holidays (month/day), so the product can поздравлять не только с ДР
    for h_date, h_title, h_tags in general_holidays_in_window(today=today, end=end):
        for client_id in client_ids[:max_holiday_recipients]:
            ev = Event(
                client_id=client_id,
                event_type="holiday",
                event_date=h_date,
                title=h_title,
                details={"holiday_tags": h_tags},
            )
            session.add(ev)
            try:
                await session.commit()
                created += 1
            except IntegrityError:
                await session.rollback()

    # Professional holidays (per client)
    for client_id, profession in prof_by_client.items():
        for h_date, h_title, h_tags in professional_holidays_for_client(
            profession=profession, today=today, end=end
        ):
            ev = Event(
                client_id=client_id,
                event_type="holiday",
                event_date=h_date,
                title=h_title,
                details={"holiday_tags": h_tags},
            )
            session.add(ev)
            try:
                await session.commit()
                created += 1
            except IntegrityError:
                await session.rollback()

    return created
