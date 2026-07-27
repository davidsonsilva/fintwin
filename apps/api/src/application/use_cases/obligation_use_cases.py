# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from src.domain.obligations.entities import FinancialObligation
from src.domain.shared.enums import Recurrence
from src.domain.shared.money import Money


class CreateObligationUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        profile_id: str,
        description: str,
        amount: Money,
        category: str,
        frequency: Recurrence,
        due_day: int,
        start_date: date,
        end_date: Optional[date],
        essential: bool,
        debt_related: bool,
    ) -> FinancialObligation:
        obligation = FinancialObligation(
            id=str(uuid4()),
            profile_id=profile_id,
            description=description,
            amount=amount,
            category=category,
            frequency=frequency,
            due_day=due_day,
            start_date=start_date,
            end_date=end_date,
            essential=essential,
            debt_related=debt_related,
        )
        self._repo.add(obligation)
        return obligation
