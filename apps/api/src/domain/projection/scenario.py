# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Parâmetros de cenário para o motor de projeção (Spec seção 10.1/10.2/10.3).

O cenário personalizado (seção 10.4) é a VS-07.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.domain.shared.enums import ScenarioType
from src.domain.shared.money import Money


@dataclass(frozen=True)
class ScenarioParameters:
    scenario_type: ScenarioType
    income_multiplier: Decimal
    essential_expense_multiplier: Decimal
    nonessential_expense_multiplier: Decimal
    unexpected_expense: Money

    @classmethod
    def probable(cls, currency: str) -> "ScenarioParameters":
        return cls(
            scenario_type=ScenarioType.PROBABLE,
            income_multiplier=Decimal("1.00"),
            essential_expense_multiplier=Decimal("1.00"),
            nonessential_expense_multiplier=Decimal("1.00"),
            unexpected_expense=Money(Decimal("0"), currency),
        )

    @classmethod
    def adverse(cls, currency: str) -> "ScenarioParameters":
        return cls(
            scenario_type=ScenarioType.ADVERSE,
            income_multiplier=Decimal("0.75"),
            essential_expense_multiplier=Decimal("1.05"),
            nonessential_expense_multiplier=Decimal("0.90"),
            unexpected_expense=Money(Decimal("0"), currency),
        )

    @classmethod
    def income_loss(cls, currency: str) -> "ScenarioParameters":
        return cls(
            scenario_type=ScenarioType.INCOME_LOSS,
            income_multiplier=Decimal("0.00"),
            essential_expense_multiplier=Decimal("1.00"),
            nonessential_expense_multiplier=Decimal("0.70"),
            unexpected_expense=Money(Decimal("0"), currency),
        )
