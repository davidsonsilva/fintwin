"""Motor do Índice de Autonomia Financeira (Spec seção 9), puro e determinístico.

Reaproveita o motor de projeção da VS-04 (`project_cashflow`) para calcular a
queima mensal ajustada por cenário, em vez de duplicar a lógica de despesas.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from src.domain.autonomy.entities import AutonomyResult
from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.projection.engine import project_cashflow
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.domain.shared.recurrence import monthly_equivalent


def _sum_money(currency: str, values: list[Money]) -> Money:
    total = Money(Decimal("0"), currency)
    for value in values:
        total = total.add(value)
    return total


def _autonomy_months(eligible_assets: Money, monthly_burn: Money) -> Optional[Decimal]:
    if monthly_burn.amount <= 0:
        return None
    return eligible_assets.amount / monthly_burn.amount


def _scenario_burn(
    scenario: ScenarioParameters,
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
    today: Optional[date],
    expense_reduction_capacity: Optional[Percentage],
) -> Money:
    projection = project_cashflow(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        horizon_months=1,
        scenario=scenario,
        currency=currency,
        today=today,
    )
    burn = projection.periods[0].expense_total
    if expense_reduction_capacity is not None:
        burn = burn.multiply(Decimal("1") - expense_reduction_capacity.as_fraction())
    return burn


def calculate_autonomy(
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
    expense_reduction_capacity: Optional[Percentage] = None,
    today: Optional[date] = None,
) -> AutonomyResult:
    eligible_accounts = [account for account in accounts if account.eligible_for_autonomy]
    eligible_assets = _sum_money(currency, [account.balance for account in eligible_accounts])

    essential_obligations = [obligation for obligation in obligations if obligation.essential]
    essential_monthly_values = [
        monthly
        for obligation in essential_obligations
        if (monthly := monthly_equivalent(obligation.amount, obligation.frequency)) is not None
    ]
    essential_expenses_monthly = _sum_money(currency, essential_monthly_values)

    basic_autonomy_months = _autonomy_months(eligible_assets, essential_expenses_monthly)

    probable_burn = _scenario_burn(
        ScenarioParameters.probable(currency),
        accounts,
        incomes,
        obligations,
        debts,
        goals,
        events,
        currency,
        today,
        expense_reduction_capacity,
    )
    adverse_burn = _scenario_burn(
        ScenarioParameters.adverse(currency),
        accounts,
        incomes,
        obligations,
        debts,
        goals,
        events,
        currency,
        today,
        expense_reduction_capacity,
    )
    income_loss_burn = _scenario_burn(
        ScenarioParameters.income_loss(currency),
        accounts,
        incomes,
        obligations,
        debts,
        goals,
        events,
        currency,
        today,
        expense_reduction_capacity,
    )

    assumptions = [
        "Autonomia básica considera apenas despesas essenciais recorrentes (sem dívidas, metas ou eventos).",
        "Autonomia ajustada usa a queima mensal projetada (motor da VS-04) sob cada cenário, incluindo "
        "dívidas, metas e eventos do primeiro mês.",
        (
            f"Capacidade declarada de redução de despesas aplicada: "
            f"{expense_reduction_capacity.as_display_percent()}%."
            if expense_reduction_capacity is not None
            else "Nenhuma capacidade de redução de despesas foi declarada no perfil."
        ),
        "Concentração de renda e número de dependentes não são incorporados nesta versão "
        "por não haver fórmula definida na especificação.",
    ]

    return AutonomyResult(
        eligible_assets=eligible_assets,
        essential_expenses_monthly=essential_expenses_monthly,
        basic_autonomy_months=basic_autonomy_months,
        probable_monthly_burn=probable_burn,
        adverse_monthly_burn=adverse_burn,
        income_loss_monthly_burn=income_loss_burn,
        probable_autonomy_months=_autonomy_months(eligible_assets, probable_burn),
        adverse_autonomy_months=_autonomy_months(eligible_assets, adverse_burn),
        income_loss_autonomy_months=_autonomy_months(eligible_assets, income_loss_burn),
        eligible_accounts=eligible_accounts,
        essential_obligations=essential_obligations,
        assumptions=assumptions,
    )
