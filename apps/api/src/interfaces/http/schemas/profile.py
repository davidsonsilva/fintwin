# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.domain.financial_profile.entities import FinancialProfile


class ProfileCreateRequest(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    dependents: int = Field(default=0, ge=0)
    monthly_expense_reduction_capacity: Optional[Decimal] = Field(default=None, ge=0, le=1)


class ProfileResponse(BaseModel):
    id: str
    currency: str
    dependents: int
    monthly_expense_reduction_capacity: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, profile: FinancialProfile) -> "ProfileResponse":
        return cls(
            id=profile.id,
            currency=profile.currency,
            dependents=profile.dependents,
            monthly_expense_reduction_capacity=(
                profile.monthly_expense_reduction_capacity.as_fraction()
                if profile.monthly_expense_reduction_capacity is not None
                else None
            ),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
