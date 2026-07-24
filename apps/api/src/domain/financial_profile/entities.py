"""Entidades do agregado FinancialProfile (Spec seção 15.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.domain.shared.enums import LiquidityType
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage


@dataclass
class FinancialProfile:
    id: str
    currency: str
    dependents: int
    monthly_expense_reduction_capacity: Optional[Percentage]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("FinancialProfile requer id.")
        if not self.currency:
            raise ValueError("FinancialProfile requer currency.")
        if self.dependents < 0:
            raise ValueError("dependents não pode ser negativo.")


@dataclass
class FinancialAccount:
    id: str
    profile_id: str
    description: str
    balance: Money
    liquidity_type: LiquidityType
    eligible_for_autonomy: bool

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("FinancialAccount requer description.")
        if not self.profile_id:
            raise ValueError("FinancialAccount requer profile_id.")
