# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Agrupamento das entidades financeiras de um perfil, usado pelo simulador de decisões."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource


@dataclass
class DecisionContext:
    accounts: list[FinancialAccount] = field(default_factory=list)
    incomes: list[IncomeSource] = field(default_factory=list)
    obligations: list[FinancialObligation] = field(default_factory=list)
    debts: list[Debt] = field(default_factory=list)
    goals: list[FinancialGoal] = field(default_factory=list)
    events: list[FinancialEvent] = field(default_factory=list)

    def copy(self) -> "DecisionContext":
        return DecisionContext(
            accounts=list(self.accounts),
            incomes=list(self.incomes),
            obligations=list(self.obligations),
            debts=list(self.debts),
            goals=list(self.goals),
            events=list(self.events),
        )
