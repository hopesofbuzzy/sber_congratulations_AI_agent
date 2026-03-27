from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    greeting_id: int
    outcome: str = Field(default="unknown", max_length=50)
    score: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class FeedbackOut(BaseModel):
    id: int
    greeting_id: int
    outcome: str
    score: int | None
    notes: str | None
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)
