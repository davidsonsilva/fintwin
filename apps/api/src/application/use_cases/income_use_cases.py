from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from src.domain.obligations.entities import IncomeSource
from src.domain.shared.enums import IncomeStability, Recurrence
from src.domain.shared.money import Money


class CreateIncomeSourceUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        profile_id: str,
        description: str,
        amount: Money,
        frequency: Recurrence,
        start_date: date,
        end_date: Optional[date],
        stability: IncomeStability,
    ) -> IncomeSource:
        income = IncomeSource(
            id=str(uuid4()),
            profile_id=profile_id,
            description=description,
            amount=amount,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            stability=stability,
        )
        self._repo.add(income)
        return income
