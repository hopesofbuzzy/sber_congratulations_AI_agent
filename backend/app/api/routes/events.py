from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event
from app.db.session import get_session
from app.schemas.events import EventOut, ManualEventCreate
from app.services.manual_events import create_manual_event_record

router = APIRouter(prefix="/events")


@router.get("", response_model=list[EventOut])
async def list_events(session: AsyncSession = Depends(get_session)) -> list[Event]:
    return (await session.execute(select(Event).order_by(Event.event_date.asc()))).scalars().all()


@router.post("/manual", response_model=EventOut)
async def create_manual_event(
    payload: ManualEventCreate, session: AsyncSession = Depends(get_session)
) -> Event:
    return await create_manual_event_record(
        session,
        client_id=payload.client_id,
        event_date=payload.event_date,
        title=payload.title,
        metadata=payload.metadata,
    )
