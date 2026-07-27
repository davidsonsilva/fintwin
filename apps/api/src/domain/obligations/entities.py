# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Entidades de renda, obrigações e dívidas (Spec seção 15.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.domain.shared.enums import IncomeStability, Recurrence
from src.domain.shared.money import Money


@dataclass
class IncomeSource:
    id: str
    profile_id: str
    description: str
    amount: Money
    frequency: Recurrence
    start_date: date
    end_date: Optional[date]
    stability: IncomeStability

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("IncomeSource requer description.")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date não pode ser anterior a start_date.")


@dataclass
class FinancialObligation:
    id: str
    profile_id: str
    description: str
    amount: Money
    category: str
    frequency: Recurrence
    due_day: int
    start_date: date
    end_date: Optional[date]
    essential: bool
    debt_related: bool

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("FinancialObligation requer description.")
        if not (1 <= self.due_day <= 31):
            raise ValueError("due_day deve estar entre 1 e 31.")


@dataclass
class Debt:
    id: str
    profile_id: str
    description: str
    outstanding_balance: Money
    installment_amount: Money
    remaining_installments: int
    interest_rate_optional: Optional[str]
    due_day: int

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("Debt requer description.")
        if self.remaining_installments < 0:
            raise ValueError("remaining_installments não pode ser negativo.")
        if not (1 <= self.due_day <= 31):
            raise ValueError("due_day deve estar entre 1 e 31.")
