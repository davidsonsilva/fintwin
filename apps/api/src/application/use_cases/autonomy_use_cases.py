"""Caso de uso do Índice de Autonomia Financeira (Spec seção 18.7)."""

from __future__ import annotations

from typing import Any, Optional

from src.domain.autonomy.engine import calculate_autonomy
from src.domain.autonomy.entities import AutonomyResult
from src.domain.shared.percentage import Percentage


class GetAutonomyUseCase:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo

    def execute(
        self,
        profile_id: str,
        currency: str,
        expense_reduction_capacity: Optional[Percentage],
    ) -> AutonomyResult:
        return calculate_autonomy(
            accounts=self._account_repo.list_by_profile(profile_id),
            incomes=self._income_repo.list_by_profile(profile_id),
            obligations=self._obligation_repo.list_by_profile(profile_id),
            debts=self._debt_repo.list_by_profile(profile_id),
            goals=self._goal_repo.list_by_profile(profile_id),
            events=self._event_repo.list_by_profile(profile_id),
            currency=currency,
            expense_reduction_capacity=expense_reduction_capacity,
        )
