# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Registro estático dos 9 tipos de decisão do simulador (Spec seção 12.1).

Segue o mesmo padrão do registro `RULES` da fragilidade (VS-06): metadados
fixos por código, sem duplicação por instância.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from src.domain.decisions import appliers
from src.domain.decisions.context import DecisionContext

Applier = Callable[[DecisionContext, Mapping[str, Any], str, Any], DecisionContext]


@dataclass(frozen=True)
class DecisionTypeDefinition:
    code: str
    title: str
    description: str
    required_parameters: tuple[str, ...]
    applier: Applier


DECISION_TYPES: dict[str, DecisionTypeDefinition] = {
    "CASH_PURCHASE": DecisionTypeDefinition(
        code="CASH_PURCHASE",
        title="Compra à vista",
        description="Um gasto pontual pago integralmente na data da decisão.",
        required_parameters=("amount", "description"),
        applier=appliers.apply_cash_purchase,
    ),
    "INSTALLMENT_PURCHASE": DecisionTypeDefinition(
        code="INSTALLMENT_PURCHASE",
        title="Compra parcelada",
        description="Uma compra dividida em parcelas iguais, com entrada opcional.",
        required_parameters=("amount", "installments", "description"),
        applier=appliers.apply_installment_purchase,
    ),
    "FINANCING": DecisionTypeDefinition(
        code="FINANCING",
        title="Financiamento",
        description="Aquisição financiada com entrada, parcelas e custos recorrentes/pontuais opcionais.",
        required_parameters=("total_amount", "installments", "description"),
        applier=appliers.apply_financing,
    ),
    "LOAN": DecisionTypeDefinition(
        code="LOAN",
        title="Empréstimo",
        description="Empréstimo em dinheiro, sem entrada, pago em parcelas.",
        required_parameters=("amount", "installments", "description"),
        applier=appliers.apply_loan,
    ),
    "INCOME_LOSS": DecisionTypeDefinition(
        code="INCOME_LOSS",
        title="Perda de renda",
        description="Interrupção total ou parcial de uma fonte de renda por um período.",
        required_parameters=("income_source_id", "months"),
        applier=appliers.apply_income_loss,
    ),
    "SALARY_REDUCTION": DecisionTypeDefinition(
        code="SALARY_REDUCTION",
        title="Redução salarial",
        description="Redução percentual de uma fonte de renda, temporária ou permanente.",
        required_parameters=("income_source_id", "reduction_pct"),
        applier=appliers.apply_salary_reduction,
    ),
    "NEW_RECURRING_EXPENSE": DecisionTypeDefinition(
        code="NEW_RECURRING_EXPENSE",
        title="Nova despesa recorrente",
        description="Uma nova obrigação financeira recorrente passa a existir.",
        required_parameters=("description", "amount", "category", "frequency"),
        applier=appliers.apply_new_recurring_expense,
    ),
    "NEW_GOAL": DecisionTypeDefinition(
        code="NEW_GOAL",
        title="Nova meta",
        description="Uma nova meta financeira com contribuição mensal passa a existir.",
        required_parameters=("description", "target_amount", "monthly_contribution"),
        applier=appliers.apply_new_goal,
    ),
    "RESERVE_INCREASE": DecisionTypeDefinition(
        code="RESERVE_INCREASE",
        title="Aumento de reserva",
        description="Um valor mensal passa a ser reservado, reduzindo o saldo disponível.",
        required_parameters=("monthly_amount",),
        applier=appliers.apply_reserve_increase,
    ),
}
