# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from src.domain.obligations.entities import Debt
from src.domain.shared.money import Money


class CreateDebtUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        profile_id: str,
        description: str,
        outstanding_balance: Money,
        installment_amount: Money,
        remaining_installments: int,
        interest_rate_optional: Optional[str],
        due_day: int,
    ) -> Debt:
        debt = Debt(
            id=str(uuid4()),
            profile_id=profile_id,
            description=description,
            outstanding_balance=outstanding_balance,
            installment_amount=installment_amount,
            remaining_installments=remaining_installments,
            interest_rate_optional=interest_rate_optional,
            due_day=due_day,
        )
        self._repo.add(debt)
        return debt
