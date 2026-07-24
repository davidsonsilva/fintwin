"""Motor do simulador de decisões (Spec seção 12), puro e determinístico.

Reaproveita o motor de projeção (VS-04, `project_cashflow`) e o motor de
autonomia (VS-05, `calculate_autonomy`) tanto para o cenário-base quanto para
o cenário simulado — nenhuma lógica financeira é duplicada aqui.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Optional

from src.domain.autonomy.engine import calculate_autonomy
from src.domain.autonomy.entities import AutonomyResult
from src.domain.decisions.context import DecisionContext
from src.domain.decisions.scenario_override import ScenarioOverride
from src.domain.decisions.types import DECISION_TYPES
from src.domain.projection.engine import project_cashflow
from src.domain.projection.entities import ProjectionResult
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.money import Money

_TOTAL_COST_TYPES = {"FINANCING", "LOAN", "INSTALLMENT_PURCHASE"}


def _money_dict(money: Money) -> dict[str, str]:
    return {"amount": money.to_json(), "currency": money.currency}


def _decimal_str(value: Optional[Decimal]) -> Optional[str]:
    return str(value) if value is not None else None


def _projection_summary(result: ProjectionResult) -> dict[str, Any]:
    return {
        "scenario": result.scenario.value,
        "first_deficit_period": result.first_deficit_period,
        "lowest_balance": _money_dict(result.lowest_balance),
        "final_balance": _money_dict(result.final_balance),
        "total_income": _money_dict(result.total_income),
        "total_expenses": _money_dict(result.total_expenses),
    }


def _autonomy_summary(result: AutonomyResult) -> dict[str, Any]:
    return {
        "basic_autonomy_months": _decimal_str(result.basic_autonomy_months),
        "probable_autonomy_months": _decimal_str(result.probable_autonomy_months),
        "adverse_autonomy_months": _decimal_str(result.adverse_autonomy_months),
        "income_loss_autonomy_months": _decimal_str(result.income_loss_autonomy_months),
    }


def _goal_months_to_target(goal, monthly_contribution: Money) -> Optional[int]:
    remaining = goal.target_amount.amount - goal.current_amount.amount
    if remaining <= 0:
        return 0
    if monthly_contribution.amount <= 0:
        return None
    return math.ceil(remaining / monthly_contribution.amount)


def _main_goal_delay_months(baseline_context: DecisionContext, simulated_context: DecisionContext) -> Optional[int]:
    def main_goal(goals):
        return min(goals, key=lambda g: g.priority) if goals else None

    base_goal = main_goal(baseline_context.goals)
    sim_goal = main_goal(simulated_context.goals)
    if base_goal is None and sim_goal is None:
        return None

    base_months = _goal_months_to_target(base_goal, base_goal.monthly_contribution) if base_goal else None
    sim_months = _goal_months_to_target(sim_goal, sim_goal.monthly_contribution) if sim_goal else None

    if base_months is None or sim_months is None:
        return None
    return sim_months - base_months


def _total_cost(decision_type: str, parameters: Mapping[str, Any], currency: str) -> Optional[dict[str, Any]]:
    if decision_type not in _TOTAL_COST_TYPES:
        return None

    zero = Money(Decimal("0"), currency)
    down_payment = Money(Decimal(str(parameters.get("down_payment", 0))), currency)

    total_amount = Decimal(str(parameters.get("total_amount", parameters.get("amount", 0))))
    installments = int(parameters.get("installments", 0))
    financed = total_amount - down_payment.amount
    installments_total = (
        Money((financed / installments).quantize(Decimal("0.01")) * installments, currency)
        if installments > 0 and financed > 0
        else zero
    )

    recurring_total = zero
    for cost in parameters.get("recurring_costs", []):
        recurring_total = recurring_total.add(Money(Decimal(str(cost["amount"])), currency))

    one_off_total = zero
    for cost in parameters.get("one_off_costs", []):
        one_off_total = one_off_total.add(Money(Decimal(str(cost["amount"])), currency))

    total = down_payment.add(installments_total).add(recurring_total).add(one_off_total)

    return {
        "down_payment": _money_dict(down_payment),
        "installments_total": _money_dict(installments_total),
        "recurring_costs_total": _money_dict(recurring_total),
        "one_off_costs_total": _money_dict(one_off_total),
        "total_cost": _money_dict(total),
    }


@dataclass
class SimulationOutcome:
    baseline_result: dict[str, Any]
    simulated_result: dict[str, Any]
    impact: dict[str, Any]
    total_cost: Optional[dict[str, Any]]
    assumptions: list[str]


def simulate_decision(
    context: DecisionContext,
    decision_type: str,
    parameters: Mapping[str, Any],
    scenario_override: Optional[ScenarioOverride],
    horizon_months: int,
    currency: str,
    today: Optional[date] = None,
) -> SimulationOutcome:
    today = today or date.today()
    definition = DECISION_TYPES[decision_type]

    baseline_context = context.copy()
    baseline_scenario = ScenarioParameters.probable(currency)
    baseline_projection = project_cashflow(
        accounts=baseline_context.accounts,
        incomes=baseline_context.incomes,
        obligations=baseline_context.obligations,
        debts=baseline_context.debts,
        goals=baseline_context.goals,
        events=baseline_context.events,
        horizon_months=horizon_months,
        scenario=baseline_scenario,
        currency=currency,
        today=today,
    )
    baseline_autonomy = calculate_autonomy(
        accounts=baseline_context.accounts,
        incomes=baseline_context.incomes,
        obligations=baseline_context.obligations,
        debts=baseline_context.debts,
        goals=baseline_context.goals,
        events=baseline_context.events,
        currency=currency,
        today=today,
    )

    simulated_context = definition.applier(context, parameters, currency, today)
    simulated_scenario = (
        scenario_override.to_scenario_parameters(currency) if scenario_override is not None else ScenarioParameters.probable(currency)
    )
    simulated_projection = project_cashflow(
        accounts=simulated_context.accounts,
        incomes=simulated_context.incomes,
        obligations=simulated_context.obligations,
        debts=simulated_context.debts,
        goals=simulated_context.goals,
        events=simulated_context.events,
        horizon_months=horizon_months,
        scenario=simulated_scenario,
        currency=currency,
        today=today,
    )
    expense_reduction_capacity = scenario_override.expense_reduction_capacity if scenario_override is not None else None
    simulated_autonomy = calculate_autonomy(
        accounts=simulated_context.accounts,
        incomes=simulated_context.incomes,
        obligations=simulated_context.obligations,
        debts=simulated_context.debts,
        goals=simulated_context.goals,
        events=simulated_context.events,
        currency=currency,
        expense_reduction_capacity=expense_reduction_capacity,
        today=today,
    )

    autonomy_delta_months = None
    if baseline_autonomy.probable_autonomy_months is not None and simulated_autonomy.probable_autonomy_months is not None:
        autonomy_delta_months = str(
            simulated_autonomy.probable_autonomy_months - baseline_autonomy.probable_autonomy_months
        )

    impact = {
        "autonomy_delta_months": autonomy_delta_months,
        "closing_balance_delta": simulated_projection.final_balance.subtract(baseline_projection.final_balance).to_json(),
        "new_first_deficit_period": (
            simulated_projection.first_deficit_period
            if simulated_projection.first_deficit_period != baseline_projection.first_deficit_period
            else None
        ),
        "goal_delay_months": _main_goal_delay_months(baseline_context, simulated_context),
    }

    assumptions = [
        "Cenário-base sempre usa o cenário provável (seção 10.1), sem o efeito da decisão.",
        "Cenário simulado usa o cenário personalizado informado (seção 10.4) quando fornecido, "
        "senão também o cenário provável — apenas com o efeito da decisão aplicado.",
    ]
    if decision_type in _TOTAL_COST_TYPES:
        assumptions.append(
            "Custo de oportunidade não é calculado nesta versão: a especificação não define a fórmula "
            "quando existe taxa informada, apenas que 'poderá ser calculada'. A taxa informada (se houver) "
            "é exposta como evidência crua, sem cálculo derivado."
        )

    return SimulationOutcome(
        baseline_result=_projection_summary(baseline_projection) | _autonomy_summary(baseline_autonomy),
        simulated_result=_projection_summary(simulated_projection) | _autonomy_summary(simulated_autonomy),
        impact=impact,
        total_cost=_total_cost(decision_type, parameters, currency),
        assumptions=assumptions,
    )
