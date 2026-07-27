# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from src.domain.obligations.entities import IncomeSource
from src.domain.shared.enums import IncomeStability, Recurrence
from src.interfaces.http.schemas.common import MoneySchema


class IncomeCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    amount: MoneySchema
    frequency: Recurrence
    start_date: date
    end_date: Optional[date] = None
    stability: IncomeStability


class IncomeResponse(BaseModel):
    id: str
    profile_id: str
    description: str
    amount: MoneySchema
    frequency: Recurrence
    start_date: date
    end_date: Optional[date]
    stability: IncomeStability

    @classmethod
    def from_domain(cls, income: IncomeSource) -> "IncomeResponse":
        return cls(
            id=income.id,
            profile_id=income.profile_id,
            description=income.description,
            amount=MoneySchema.from_domain(income.amount),
            frequency=income.frequency,
            start_date=income.start_date,
            end_date=income.end_date,
            stability=income.stability,
        )
