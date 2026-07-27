# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Caso de uso de projeção de fluxo de caixa (Spec seção 18.6): carrega as
entidades já persistidas e delega o cálculo ao motor de domínio puro.
"""

from __future__ import annotations

from typing import Any

from src.domain.projection.engine import project_cashflow
from src.domain.projection.entities import ProjectionResult
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import ScenarioType


class GetProjectionUseCase:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo

    def execute(
        self,
        profile_id: str,
        currency: str,
        horizon_months: int,
        scenario_type: ScenarioType,
    ) -> ProjectionResult:
        scenario = (
            ScenarioParameters.probable(currency)
            if scenario_type == ScenarioType.PROBABLE
            else ScenarioParameters.adverse(currency)
        )

        return project_cashflow(
            accounts=self._account_repo.list_by_profile(profile_id),
            incomes=self._income_repo.list_by_profile(profile_id),
            obligations=self._obligation_repo.list_by_profile(profile_id),
            debts=self._debt_repo.list_by_profile(profile_id),
            goals=self._goal_repo.list_by_profile(profile_id),
            events=self._event_repo.list_by_profile(profile_id),
            horizon_months=horizon_months,
            scenario=scenario,
            currency=currency,
        )
