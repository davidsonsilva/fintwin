"""Entidade FinancialEvent, usada na projeção de fluxo de caixa (Spec seção 15.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.domain.shared.enums import Direction, Recurrence
from src.domain.shared.money import Money


@dataclass
class FinancialEvent:
    id: str
    profile_id: str
    description: str
    event_type: str
    amount: Money
    date: date
    recurrence: Optional[Recurrence]
    direction: Direction

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("FinancialEvent requer description.")
        if not self.event_type:
            raise ValueError("FinancialEvent requer event_type.")
