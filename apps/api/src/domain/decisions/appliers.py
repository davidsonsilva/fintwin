# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Appliers puros dos 9 tipos de decisão do simulador (Spec seção 12.1).

Cada applier recebe o `DecisionContext` atual (já uma cópia — nunca mutado)
e os parâmetros brutos da decisão, e devolve um novo `DecisionContext` com o
efeito da decisão aplicado, para ser passado ao motor de projeção (VS-04) e
autonomia (VS-05) sem nenhuma mudança nesses motores.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Mapping
from uuid import uuid4

from src.domain.decisions.context import DecisionContext
from src.domain.decisions.entities import FinancialGoal
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.cashflow.entities import FinancialEvent
from src.domain.shared.enums import Direction, Recurrence
from src.domain.shared.money import Money


def _money(value: Any, currency: str) -> Money:
    return Money(Decimal(str(value)), currency)


def _new_event(
    context: DecisionContext,
    description: str,
    amount: Money,
    direction: Direction,
    event_date: date,
    event_type: str,
) -> None:
    context.events.append(
        FinancialEvent(
            id=str(uuid4()),
            profile_id="",
            description=description,
            event_type=event_type,
            amount=amount,
            date=event_date,
            recurrence=None,
            direction=direction,
        )
    )


def apply_cash_purchase(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    context = context.copy()
    purchase_date = date.fromisoformat(parameters["date"]) if parameters.get("date") else today
    _new_event(
        context,
        description=parameters.get("description", "Compra à vista"),
        amount=_money(parameters["amount"], currency),
        direction=Direction.EXPENSE,
        event_date=purchase_date,
        event_type=parameters.get("category", "purchase"),
    )
    return context


def apply_installment_purchase(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    context = context.copy()
    total = Decimal(str(parameters["amount"]))
    down_payment = Decimal(str(parameters.get("down_payment", 0)))
    installments = int(parameters["installments"])
    financed = total - down_payment

    if down_payment > 0:
        _new_event(
            context,
            description=f"Entrada — {parameters.get('description', 'Compra parcelada')}",
            amount=_money(down_payment, currency),
            direction=Direction.EXPENSE,
            event_date=today,
            event_type="down_payment",
        )

    if installments > 0 and financed > 0:
        installment_amount = (financed / installments).quantize(Decimal("0.01"))
        context.debts.append(
            Debt(
                id=str(uuid4()),
                profile_id="",
                description=parameters.get("description", "Compra parcelada"),
                outstanding_balance=_money(financed, currency),
                installment_amount=_money(installment_amount, currency),
                remaining_installments=installments,
                interest_rate_optional=None,
                due_day=today.day if today.day <= 28 else 28,
            )
        )
    return context


def apply_financing(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    context = context.copy()
    total_amount = Decimal(str(parameters["total_amount"]))
    down_payment = Decimal(str(parameters.get("down_payment", 0)))
    installments = int(parameters["installments"])
    financed = total_amount - down_payment
    description = parameters.get("description", "Financiamento")

    if down_payment > 0:
        _new_event(
            context,
            description=f"Entrada — {description}",
            amount=_money(down_payment, currency),
            direction=Direction.EXPENSE,
            event_date=today,
            event_type="down_payment",
        )

    if installments > 0 and financed > 0:
        installment_amount = (financed / installments).quantize(Decimal("0.01"))
        context.debts.append(
            Debt(
                id=str(uuid4()),
                profile_id="",
                description=description,
                outstanding_balance=_money(financed, currency),
                installment_amount=_money(installment_amount, currency),
                remaining_installments=installments,
                interest_rate_optional=parameters.get("interest_rate_optional"),
                due_day=today.day if today.day <= 28 else 28,
            )
        )

    for cost in parameters.get("recurring_costs", []):
        context.obligations.append(
            FinancialObligation(
                id=str(uuid4()),
                profile_id="",
                description=cost["description"],
                amount=_money(cost["amount"], currency),
                category="financing_cost",
                frequency=Recurrence.MONTHLY,
                due_day=today.day if today.day <= 28 else 28,
                start_date=today,
                end_date=None,
                essential=False,
                debt_related=True,
            )
        )

    for cost in parameters.get("one_off_costs", []):
        _new_event(
            context,
            description=cost["description"],
            amount=_money(cost["amount"], currency),
            direction=Direction.EXPENSE,
            event_date=today,
            event_type="financing_one_off_cost",
        )

    return context


def apply_loan(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    parameters = dict(parameters)
    parameters.setdefault("down_payment", 0)
    total_amount = Decimal(str(parameters.get("total_amount", parameters.get("amount"))))
    down_payment = Decimal(str(parameters["down_payment"]))
    parameters["total_amount"] = total_amount

    context = apply_financing(context, parameters, currency, today)

    financed = total_amount - down_payment
    if financed > 0:
        _new_event(
            context,
            description=f"Recebimento do empréstimo — {parameters.get('description', 'Empréstimo')}",
            amount=_money(financed, currency),
            direction=Direction.INCOME,
            event_date=today,
            event_type="loan_disbursement",
        )
    return context


def _apply_income_adjustment(context: DecisionContext, parameters: Mapping[str, Any], today: date) -> DecisionContext:
    context = context.copy()
    income_id = parameters["income_source_id"]
    reduction_pct = Decimal(str(parameters.get("reduction_pct", 1)))
    months = parameters.get("months")

    updated_incomes: list[IncomeSource] = []
    for income in context.incomes:
        if income.id != income_id:
            updated_incomes.append(income)
            continue

        reduced_amount = income.amount.multiply(Decimal("1") - reduction_pct)

        if months is None:
            updated_incomes.append(replace(income, amount=reduced_amount))
            continue

        resume_date = today + timedelta(days=30 * int(months))
        updated_incomes.append(replace(income, amount=reduced_amount, end_date=resume_date - timedelta(days=1)))
        if income.end_date is None or income.end_date >= resume_date:
            updated_incomes.append(replace(income, start_date=resume_date))

    context.incomes = updated_incomes
    return context


def apply_income_loss(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    parameters = dict(parameters)
    parameters.setdefault("reduction_pct", 1)
    return _apply_income_adjustment(context, parameters, today)


def apply_salary_reduction(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    return _apply_income_adjustment(context, parameters, today)


def apply_new_recurring_expense(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    context = context.copy()
    start_date = date.fromisoformat(parameters["start_date"]) if parameters.get("start_date") else today
    context.obligations.append(
        FinancialObligation(
            id=str(uuid4()),
            profile_id="",
            description=parameters["description"],
            amount=_money(parameters["amount"], currency),
            category=parameters.get("category", "other"),
            frequency=Recurrence(parameters.get("frequency", "monthly")),
            due_day=start_date.day if start_date.day <= 28 else 28,
            start_date=start_date,
            end_date=None,
            essential=bool(parameters.get("essential", False)),
            debt_related=False,
        )
    )
    return context


def apply_new_goal(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    context = context.copy()
    deadline = date.fromisoformat(parameters["deadline"]) if parameters.get("deadline") else None
    context.goals.append(
        FinancialGoal(
            id=str(uuid4()),
            profile_id="",
            description=parameters["description"],
            target_amount=_money(parameters["target_amount"], currency),
            current_amount=_money(parameters.get("current_amount", 0), currency),
            deadline=deadline,
            priority=int(parameters.get("priority", 1)),
            monthly_contribution=_money(parameters["monthly_contribution"], currency),
        )
    )
    return context


def apply_reserve_increase(context: DecisionContext, parameters: Mapping[str, Any], currency: str, today: date) -> DecisionContext:
    context = context.copy()
    context.obligations.append(
        FinancialObligation(
            id=str(uuid4()),
            profile_id="",
            description=parameters.get("description", "Reforço de reserva"),
            amount=_money(parameters["monthly_amount"], currency),
            category="reserve_increase",
            frequency=Recurrence.MONTHLY,
            due_day=today.day if today.day <= 28 else 28,
            start_date=today,
            end_date=None,
            essential=False,
            debt_related=False,
        )
    )
    return context
