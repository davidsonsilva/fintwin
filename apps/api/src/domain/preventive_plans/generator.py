# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Gerador de Planos Preventivos por regras fixas (Spec seção 13).

Cada código de fragilidade (`src.domain.fragility.rules.RULES`) mapeia para
uma ação e um `expected_result`, calculados a partir do mesmo `FragilityContext`
(projeção + autonomia, VS-04/VS-05/VS-06) que o próprio radar de fragilidade já
usa — evita duplicar fórmulas financeiras e mantém rastreabilidade entre a
evidência que disparou a fragilidade e a ação proposta. Textos descritivos
reaproveitam rótulos já presentes em `finding.evidence`; todo valor monetário é
recalculado a partir do contexto (nunca parseado de strings de evidência), para
refletir o estado atual do perfil no momento da geração.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, ROUND_UP, Decimal
from typing import Any, Callable, Optional
from uuid import uuid4

from src.domain.autonomy.engine import calculate_autonomy
from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.fragility.detector import FragilityContext
from src.domain.fragility.entities import FragilityFinding
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.preventive_plans.entities import PreventivePlan
from src.domain.projection.engine import project_cashflow
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import Direction, PlanStatus, Recurrence
from src.domain.shared.formatting import format_date, format_money, format_percentage
from src.domain.shared.percentage import Percentage
from src.domain.shared.money import Money

_GENERATION_HORIZON_MONTHS = 3
_DEFAULT_DUE_OFFSET_DAYS = 90
_NON_TERMINAL_STATUSES = {PlanStatus.PROPOSED, PlanStatus.APPROVED, PlanStatus.IN_PROGRESS}

_TemplateFn = Callable[[FragilityFinding, FragilityContext, str, date], "tuple[list[dict[str, Any]], dict[str, Any]]"]


def _money(amount: Decimal, currency: str) -> Money:
    return Money(amount, currency)


def _round_months(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _money_dict(money: Money) -> dict[str, str]:
    return {"amount": money.to_json(), "currency": money.currency}


def _action(description: str, impact: Optional[Money], due_date: date) -> dict[str, Any]:
    return {
        "description": description,
        "expected_monthly_impact": _money_dict(impact) if impact is not None else None,
        "due_date": due_date.isoformat(),
    }


def _expected_result(deficit_avoided: bool, autonomy_change_months: Optional[Decimal]) -> dict[str, Any]:
    return {
        "deficit_avoided": deficit_avoided,
        "autonomy_change_months": (
            str(_round_months(autonomy_change_months)) if autonomy_change_months is not None else None
        ),
    }


def _autonomy_change_from_impact(impact: Money, ctx: FragilityContext) -> Optional[Decimal]:
    essential = ctx.autonomy.essential_expenses_monthly.amount
    if essential <= 0:
        return None
    return impact.amount / essential


def _period_to_date(period: str) -> date:
    year_str, month_str = period.split("-")
    return date(int(year_str), int(month_str), 1)


def _default_due_date(today: date) -> date:
    return today + timedelta(days=_DEFAULT_DUE_OFFSET_DAYS)


def _template_income_concentration(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    main_description = finding.evidence.get("main_source_description", "a fonte principal")
    # A evidência guarda a fração como string ("0.82"), não como Percentage.
    percentage = finding.evidence.get("main_source_percentage", "")
    share = f" concentra {format_percentage(Percentage(Decimal(percentage)))} da renda mensal" if percentage else ""
    description = (
        f"Diversificar fontes de renda ou reforçar a margem de segurança: {main_description}"
        f"{share}."
    )
    actions = [_action(description, None, _default_due_date(today))]
    return actions, _expected_result(False, None)


def _template_essential_expense_ratio(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    essential = ctx.autonomy.essential_expenses_monthly.amount
    target = Decimal("0.60") * ctx.total_income_monthly.amount
    needed = max(essential - target, Decimal("0"))
    impact = _money(needed, currency)
    description = (
        f"Reduzir despesas essenciais recorrentes em {format_money(impact)} por mês para trazer o "
        "comprometimento da renda de volta a 60%."
    )
    actions = [_action(description, impact, _default_due_date(today))]
    return actions, _expected_result(False, _autonomy_change_from_impact(impact, ctx))


def _template_debt_service_ratio(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target = Decimal("0.30") * ctx.total_income_monthly.amount
    needed = max(ctx.debt_service_monthly.amount - target, Decimal("0"))
    impact = _money(needed, currency)
    description = (
        f"Priorizar a quitação de dívidas para reduzir o serviço da dívida em {format_money(impact)} por mês "
        "e voltar a 30% da renda."
    )
    actions = [_action(description, impact, _default_due_date(today))]
    # A autonomia (VS-05) é calculada só a partir de ativos elegíveis e despesas essenciais,
    # independente do serviço da dívida — mesmo achado já documentado na VS-05/VS-07.
    return actions, _expected_result(False, None)


def _template_recurring_credit_for_essentials(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    items = finding.evidence.get("obligations", [])
    description = "Revisar/renegociar as obrigações essenciais pagas via crédito recorrente: " + ", ".join(items) + "."
    actions = [_action(description, None, _default_due_date(today))]
    return actions, _expected_result(False, None)


def _template_projected_reserve_decline(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    periods = ctx.projection.periods[:3]
    total_negative = sum((period.net_cashflow.amount for period in periods), Decimal("0"))
    magnitude = abs(total_negative) / Decimal("3") if periods else Decimal("0")
    impact = _money(magnitude, currency)
    description = f"Reservar {format_money(impact)} por mês para compensar a tendência de queda projetada no fluxo de caixa."
    actions = [_action(description, impact, _default_due_date(today))]
    return actions, _expected_result(True, _autonomy_change_from_impact(impact, ctx))


def _template_concentrated_due_dates(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    items = finding.evidence.get("items", [])
    window_start = finding.evidence.get("window_start_day", "")
    description = (
        f"Reorganizar vencimentos concentrados na janela a partir do dia {window_start}: "
        + ", ".join(items)
        + "."
    )
    actions = [_action(description, None, _default_due_date(today))]
    return actions, _expected_result(False, None)


def _template_projected_deficit_90_days(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lowest = ctx.projection.lowest_balance.amount
    magnitude = abs(lowest) if lowest < 0 else Decimal("0")
    impact = _money(magnitude, currency)
    first_deficit = ctx.projection.first_deficit_period
    due_date = _period_to_date(first_deficit) if first_deficit else _default_due_date(today)
    description = (
        f"Provisionar {format_money(impact)} até {format_date(due_date)} para cobrir o déficit projetado "
        f"(saldo mínimo projetado: {format_money(ctx.projection.lowest_balance)})."
    )
    actions = [_action(description, impact, due_date)]
    return actions, _expected_result(True, _autonomy_change_from_impact(impact, ctx))


_FUNDING_PERIOD_MONTHS = Decimal(_DEFAULT_DUE_OFFSET_DAYS) / Decimal("30")


def _template_reserve_below_three_months(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    months = ctx.autonomy.basic_autonomy_months
    shortfall_months = Decimal("3") - months if months is not None else Decimal("3")
    shortfall_months = max(shortfall_months, Decimal("0"))
    due_date = _default_due_date(today)
    total_gap = shortfall_months * ctx.autonomy.essential_expenses_monthly.amount
    # Arredonda para cima: 3 aportes deste valor sempre cobrem o total_gap,
    # mesmo quando a divisão exata não é representável em centavos.
    monthly_amount = (total_gap / _FUNDING_PERIOD_MONTHS).quantize(Decimal("0.01"), rounding=ROUND_UP)
    impact = _money(monthly_amount, currency)
    description = (
        f"Aumentar a reserva de emergência em {format_money(impact)} por mês até {format_date(due_date)} "
        "para atingir 3 meses de autonomia básica."
    )
    actions = [_action(description, impact, due_date)]
    return actions, _expected_result(True, shortfall_months)


def _template_unprovisioned_annual_expense(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    total_annual = Decimal("0")
    for obligation in ctx.obligations:
        if obligation.frequency == Recurrence.YEARLY:
            total_annual += obligation.amount.amount
    for event in ctx.events:
        if event.recurrence == Recurrence.YEARLY and event.direction == Direction.EXPENSE:
            total_annual += event.amount.amount
    impact = _money(total_annual / Decimal("12"), currency)
    description = f"Provisionar {format_money(impact)} por mês para cobrir despesas anuais não provisionadas."
    actions = [_action(description, impact, _default_due_date(today))]
    return actions, _expected_result(False, None)


def _template_uncovered_future_installments(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    disposable = ctx.total_income_monthly.amount - ctx.autonomy.essential_expenses_monthly.amount
    excess = max(ctx.debt_service_monthly.amount - disposable, Decimal("0"))
    impact = _money(excess, currency)
    description = (
        f"Priorizar a quitação de dívidas: o serviço da dívida excede em {format_money(impact)} por mês a renda "
        "disponível após despesas essenciais."
    )
    actions = [_action(description, impact, _default_due_date(today))]
    return actions, _expected_result(True, None)


def _template_incompatible_goal(
    finding: FragilityFinding, ctx: FragilityContext, currency: str, today: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not ctx.goals:
        description = "Revisar metas financeiras: nenhuma meta ativa encontrada no momento da geração do plano."
        actions = [_action(description, None, _default_due_date(today))]
        return actions, _expected_result(False, None)

    top_goal = min(ctx.goals, key=lambda goal: goal.priority)
    disposable = (
        ctx.total_income_monthly.amount
        - ctx.autonomy.essential_expenses_monthly.amount
        - ctx.debt_service_monthly.amount
    )
    gap = max(top_goal.monthly_contribution.amount - disposable, Decimal("0"))
    impact = _money(gap, currency)
    description = (
        f"Ajustar a meta '{top_goal.description}': reduzir a contribuição mensal em {format_money(impact)} "
        "ou estender o prazo, para caber na renda disponível."
    )
    actions = [_action(description, impact, _default_due_date(today))]
    return actions, _expected_result(False, None)


_TEMPLATES: dict[str, _TemplateFn] = {
    "INCOME_CONCENTRATION": _template_income_concentration,
    "ESSENTIAL_EXPENSE_RATIO": _template_essential_expense_ratio,
    "DEBT_SERVICE_RATIO": _template_debt_service_ratio,
    "RECURRING_CREDIT_FOR_ESSENTIALS": _template_recurring_credit_for_essentials,
    "PROJECTED_RESERVE_DECLINE": _template_projected_reserve_decline,
    "CONCENTRATED_DUE_DATES": _template_concentrated_due_dates,
    "PROJECTED_DEFICIT_90_DAYS": _template_projected_deficit_90_days,
    "RESERVE_BELOW_THREE_MONTHS": _template_reserve_below_three_months,
    "UNPROVISIONED_ANNUAL_EXPENSE": _template_unprovisioned_annual_expense,
    "UNCOVERED_FUTURE_INSTALLMENTS": _template_uncovered_future_installments,
    "INCOMPATIBLE_GOAL": _template_incompatible_goal,
}


def generate_preventive_plans(
    findings: list[FragilityFinding],
    existing_plans: list[PreventivePlan],
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
    today: Optional[date] = None,
) -> list[PreventivePlan]:
    today = today or date.today()

    projection = project_cashflow(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        horizon_months=_GENERATION_HORIZON_MONTHS,
        scenario=ScenarioParameters.probable(currency),
        currency=currency,
        today=today,
    )
    autonomy = calculate_autonomy(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=currency,
        today=today,
    )
    context = FragilityContext(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=currency,
        projection=projection,
        autonomy=autonomy,
    )

    existing_risk_codes = {plan.risk_code for plan in existing_plans if plan.status in _NON_TERMINAL_STATUSES}

    new_plans: list[PreventivePlan] = []
    for finding in findings:
        if finding.status != "active" or finding.code in existing_risk_codes:
            continue
        template = _TEMPLATES.get(finding.code)
        if template is None:
            continue
        actions, expected_result = template(finding, context, currency, today)
        new_plans.append(
            PreventivePlan(
                id=str(uuid4()),
                profile_id=finding.profile_id,
                risk_code=finding.code,
                status=PlanStatus.PROPOSED,
                actions=actions,
                expected_result=expected_result,
                created_at=datetime.now(),
                approved_at=None,
            )
        )
    return new_plans
