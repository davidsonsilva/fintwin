from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from src.domain.obligations.entities import FinancialObligation
from src.domain.shared.enums import Recurrence
from src.interfaces.http.schemas.common import MoneySchema


class ObligationCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    amount: MoneySchema
    category: str = Field(min_length=1)
    frequency: Recurrence
    due_day: int = Field(ge=1, le=31)
    start_date: date
    end_date: Optional[date] = None
    essential: bool
    debt_related: bool = False


class ObligationResponse(BaseModel):
    id: str
    profile_id: str
    description: str
    amount: MoneySchema
    category: str
    frequency: Recurrence
    due_day: int
    start_date: date
    end_date: Optional[date]
    essential: bool
    debt_related: bool

    @classmethod
    def from_domain(cls, obligation: FinancialObligation) -> "ObligationResponse":
        return cls(
            id=obligation.id,
            profile_id=obligation.profile_id,
            description=obligation.description,
            amount=MoneySchema.from_domain(obligation.amount),
            category=obligation.category,
            frequency=obligation.frequency,
            due_day=obligation.due_day,
            start_date=obligation.start_date,
            end_date=obligation.end_date,
            essential=obligation.essential,
            debt_related=obligation.debt_related,
        )
