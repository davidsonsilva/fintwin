"""Entidades FinancialGoal e Simulation (Spec seção 15.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping, Optional

from src.domain.shared.money import Money


@dataclass
class FinancialGoal:
    id: str
    profile_id: str
    description: str
    target_amount: Money
    current_amount: Money
    deadline: Optional[date]
    priority: int
    monthly_contribution: Money

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("FinancialGoal requer description.")
        if self.priority < 1:
            raise ValueError("priority deve ser >= 1.")


@dataclass
class Simulation:
    id: str
    profile_id: str
    type: str
    parameters: Mapping[str, Any]
    baseline_result: Mapping[str, Any]
    simulated_result: Mapping[str, Any]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.type:
            raise ValueError("Simulation requer type.")
