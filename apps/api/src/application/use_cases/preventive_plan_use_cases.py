# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Casos de uso dos Planos Preventivos (Spec seção 18.10)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from src.domain.preventive_plans.entities import PreventivePlan
from src.domain.preventive_plans.generator import generate_preventive_plans
from src.domain.preventive_plans.validation import validate_status_transition
from src.domain.shared.enums import PlanStatus


class PreventivePlanNotFoundError(ValueError):
    pass


class GeneratePreventivePlansUseCase:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
        fragility_repo: Any,
        plan_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo
        self._fragility_repo = fragility_repo
        self._plan_repo = plan_repo

    def execute(self, profile_id: str, currency: str) -> list[PreventivePlan]:
        accounts = self._account_repo.list_by_profile(profile_id)
        incomes = self._income_repo.list_by_profile(profile_id)
        obligations = self._obligation_repo.list_by_profile(profile_id)
        debts = self._debt_repo.list_by_profile(profile_id)
        goals = self._goal_repo.list_by_profile(profile_id)
        events = self._event_repo.list_by_profile(profile_id)
        findings = self._fragility_repo.list_by_profile(profile_id)
        existing_plans = self._plan_repo.list_by_profile(profile_id)

        new_plans = generate_preventive_plans(
            findings=findings,
            existing_plans=existing_plans,
            accounts=accounts,
            incomes=incomes,
            obligations=obligations,
            debts=debts,
            goals=goals,
            events=events,
            currency=currency,
        )
        for plan in new_plans:
            self._plan_repo.add(plan)
        return new_plans


class ListPreventivePlansUseCase:
    def __init__(self, plan_repo: Any) -> None:
        self._plan_repo = plan_repo

    def execute(self, profile_id: str, status: Optional[PlanStatus] = None) -> list[PreventivePlan]:
        plans = self._plan_repo.list_by_profile(profile_id)
        if status is not None:
            plans = [plan for plan in plans if plan.status == status]
        return plans


class UpdatePlanStatusUseCase:
    def __init__(self, plan_repo: Any) -> None:
        self._plan_repo = plan_repo

    def execute(self, plan_id: str, new_status: PlanStatus) -> PreventivePlan:
        plan = self._plan_repo.get(plan_id)
        if plan is None:
            raise PreventivePlanNotFoundError(f"Plano não encontrado: {plan_id!r}")

        validate_status_transition(plan.status, new_status)

        approved_at = plan.approved_at
        if new_status == PlanStatus.APPROVED:
            approved_at = datetime.now()

        updated_plan = PreventivePlan(
            id=plan.id,
            profile_id=plan.profile_id,
            risk_code=plan.risk_code,
            status=new_status,
            actions=plan.actions,
            expected_result=plan.expected_result,
            created_at=plan.created_at,
            approved_at=approved_at,
        )
        self._plan_repo.update(updated_plan)
        return updated_plan
