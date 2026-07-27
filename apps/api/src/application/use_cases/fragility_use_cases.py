# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Casos de uso do Radar de Fragilidade (Spec seção 18.8)."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from src.domain.autonomy.engine import calculate_autonomy
from src.domain.fragility.detector import detect_fragilities
from src.domain.fragility.entities import FragilityFinding
from src.domain.projection.engine import project_cashflow
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import Severity
from src.domain.shared.percentage import Percentage

_DETECTION_HORIZON_MONTHS = 3


class DetectFragilitiesUseCase:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
        fragility_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo
        self._fragility_repo = fragility_repo

    def execute(
        self,
        profile_id: str,
        currency: str,
        expense_reduction_capacity: Optional[Percentage],
    ) -> list[FragilityFinding]:
        accounts = self._account_repo.list_by_profile(profile_id)
        incomes = self._income_repo.list_by_profile(profile_id)
        obligations = self._obligation_repo.list_by_profile(profile_id)
        debts = self._debt_repo.list_by_profile(profile_id)
        goals = self._goal_repo.list_by_profile(profile_id)
        events = self._event_repo.list_by_profile(profile_id)

        projection = project_cashflow(
            accounts=accounts,
            incomes=incomes,
            obligations=obligations,
            debts=debts,
            goals=goals,
            events=events,
            horizon_months=_DETECTION_HORIZON_MONTHS,
            scenario=ScenarioParameters.probable(currency),
            currency=currency,
        )
        autonomy = calculate_autonomy(
            accounts=accounts,
            incomes=incomes,
            obligations=obligations,
            debts=debts,
            goals=goals,
            events=events,
            currency=currency,
            expense_reduction_capacity=expense_reduction_capacity,
        )

        detected = detect_fragilities(
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

        self._fragility_repo.delete_all_by_profile(profile_id)

        today = date.today()
        findings = [
            FragilityFinding(
                id=str(uuid4()),
                profile_id=profile_id,
                code=detected_item.code,
                severity=detected_item.severity,
                evidence=detected_item.evidence,
                detected_at=today,
                status="active",
            )
            for detected_item in detected
        ]
        for finding in findings:
            self._fragility_repo.add(finding)
        return findings


class ListFragilitiesUseCase:
    def __init__(self, fragility_repo: Any) -> None:
        self._fragility_repo = fragility_repo

    def execute(
        self,
        profile_id: str,
        severity: Optional[Severity] = None,
        code: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[FragilityFinding]:
        findings = self._fragility_repo.list_by_profile(profile_id)
        if severity is not None:
            findings = [finding for finding in findings if finding.severity == severity]
        if code is not None:
            findings = [finding for finding in findings if finding.code == code]
        if status is not None:
            findings = [finding for finding in findings if finding.status == status]
        return findings
