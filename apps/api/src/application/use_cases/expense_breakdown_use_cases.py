# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Distribuição das despesas mensais por categoria (linha de gráficos do dashboard)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.domain.obligations.entities import FinancialObligation
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.domain.shared.recurrence import monthly_equivalent


@dataclass
class CategoryBreakdown:
    category: str
    amount: Money
    percentage: Percentage


class GetExpenseBreakdownByCategoryUseCase:
    def __init__(self, obligation_repo: Any) -> None:
        self._obligation_repo = obligation_repo

    def execute(self, profile_id: str, currency: str) -> list[CategoryBreakdown]:
        obligations: list[FinancialObligation] = self._obligation_repo.list_by_profile(profile_id)

        totals: dict[str, Money] = {}
        for obligation in obligations:
            monthly = monthly_equivalent(obligation.amount, obligation.frequency)
            if monthly is None:
                continue
            # Money.add() rejeita moedas diferentes (CurrencyMismatchError), então uma
            # obrigação em moeda distinta da do perfil estoura em vez de inflar o total.
            existing = totals.get(obligation.category, Money(Decimal("0"), currency))
            totals[obligation.category] = existing.add(monthly)

        grand_total = sum((money.amount for money in totals.values()), Decimal("0"))

        breakdown = [
            CategoryBreakdown(
                category=category,
                amount=money,
                percentage=Percentage(money.amount / grand_total if grand_total > 0 else Decimal("0")),
            )
            for category, money in totals.items()
        ]
        return sorted(breakdown, key=lambda item: item.amount.amount, reverse=True)
