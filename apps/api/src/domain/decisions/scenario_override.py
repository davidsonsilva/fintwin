"""Cenário personalizado do simulador de decisões (Spec seção 10.4)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import ScenarioType
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage


@dataclass(frozen=True)
class ScenarioOverride:
    income_multiplier: Optional[Decimal] = None
    essential_expense_multiplier: Optional[Decimal] = None
    nonessential_expense_multiplier: Optional[Decimal] = None
    unexpected_expense: Optional[Money] = None
    expense_reduction_capacity: Optional[Percentage] = None

    def to_scenario_parameters(self, currency: str) -> ScenarioParameters:
        probable = ScenarioParameters.probable(currency)
        return ScenarioParameters(
            scenario_type=ScenarioType.CUSTOM,
            income_multiplier=self.income_multiplier if self.income_multiplier is not None else probable.income_multiplier,
            essential_expense_multiplier=(
                self.essential_expense_multiplier
                if self.essential_expense_multiplier is not None
                else probable.essential_expense_multiplier
            ),
            nonessential_expense_multiplier=(
                self.nonessential_expense_multiplier
                if self.nonessential_expense_multiplier is not None
                else probable.nonessential_expense_multiplier
            ),
            unexpected_expense=self.unexpected_expense if self.unexpected_expense is not None else probable.unexpected_expense,
        )
