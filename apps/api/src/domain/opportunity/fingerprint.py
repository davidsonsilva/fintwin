# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Impressão digital dos dados financeiros que alimentam uma análise.

Serve a uma pergunta só: *os dados mudaram desde que esta recomendação foi
gerada?* Se mudaram, a tela marca a análise como defasada e pede recálculo
antes da aprovação — em vez de recalcular sozinha e trocar os números debaixo
do usuário.

Só entram campos que o motor de oportunidade realmente lê. Renomear a
descrição de uma conta não invalida uma recomendação; mudar o saldo dela sim.
"""

from __future__ import annotations

import hashlib
from typing import Iterable

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource


def _join(parts: Iterable[str]) -> str:
    return "|".join(sorted(parts))


def compute_input_fingerprint(
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
) -> str:
    blocks = [
        currency,
        _join(f"a:{a.id}:{a.balance.amount}:{a.eligible_for_autonomy}" for a in accounts),
        _join(f"i:{i.id}:{i.amount.amount}:{i.frequency.value}:{i.stability.value}" for i in incomes),
        _join(
            f"o:{o.id}:{o.amount.amount}:{o.frequency.value}:{o.essential}:{o.category}"
            for o in obligations
        ),
        _join(f"d:{d.id}:{d.installment_amount.amount}:{d.remaining_installments}" for d in debts),
        _join(
            f"g:{g.id}:{g.target_amount.amount}:{g.current_amount.amount}:"
            f"{g.monthly_contribution.amount}:{g.priority}"
            for g in goals
        ),
        _join(f"e:{e.id}:{e.amount.amount}:{e.date.isoformat()}:{e.direction.value}" for e in events),
    ]
    return hashlib.sha256("\n".join(blocks).encode("utf-8")).hexdigest()
