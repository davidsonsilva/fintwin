from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.domain.financial_profile.entities import FinancialAccount
from src.domain.shared.enums import LiquidityType
from src.domain.shared.money import Money


class CreateAccountUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        profile_id: str,
        description: str,
        balance: Money,
        liquidity_type: LiquidityType,
        eligible_for_autonomy: bool,
    ) -> FinancialAccount:
        account = FinancialAccount(
            id=str(uuid4()),
            profile_id=profile_id,
            description=description,
            balance=balance,
            liquidity_type=liquidity_type,
            eligible_for_autonomy=eligible_for_autonomy,
        )
        self._repo.add(account)
        return account
