from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from src.domain.cashflow.entities import FinancialEvent
from src.domain.shared.enums import Direction, Recurrence
from src.interfaces.http.schemas.common import MoneySchema


class EventCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    amount: MoneySchema
    date: date
    recurrence: Optional[Recurrence] = None
    direction: Direction


class EventResponse(BaseModel):
    id: str
    profile_id: str
    description: str
    event_type: str
    amount: MoneySchema
    date: date
    recurrence: Optional[Recurrence]
    direction: Direction

    @classmethod
    def from_domain(cls, event: FinancialEvent) -> "EventResponse":
        return cls(
            id=event.id,
            profile_id=event.profile_id,
            description=event.description,
            event_type=event.event_type,
            amount=MoneySchema.from_domain(event.amount),
            date=event.date,
            recurrence=event.recurrence,
            direction=event.direction,
        )
