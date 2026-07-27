# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.domain.obligations.entities import Debt
from src.interfaces.http.schemas.common import MoneySchema


class DebtCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    outstanding_balance: MoneySchema
    installment_amount: MoneySchema
    remaining_installments: int = Field(ge=0)
    interest_rate_optional: Optional[str] = None
    due_day: int = Field(ge=1, le=31)


class DebtResponse(BaseModel):
    id: str
    profile_id: str
    description: str
    outstanding_balance: MoneySchema
    installment_amount: MoneySchema
    remaining_installments: int
    interest_rate_optional: Optional[str]
    due_day: int

    @classmethod
    def from_domain(cls, debt: Debt) -> "DebtResponse":
        return cls(
            id=debt.id,
            profile_id=debt.profile_id,
            description=debt.description,
            outstanding_balance=MoneySchema.from_domain(debt.outstanding_balance),
            installment_amount=MoneySchema.from_domain(debt.installment_amount),
            remaining_installments=debt.remaining_installments,
            interest_rate_optional=debt.interest_rate_optional,
            due_day=debt.due_day,
        )
