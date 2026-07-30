# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Casos de uso do perfil financeiro: sem delete, um perfil por fluxo de onboarding."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from src.domain.financial_profile.entities import FinancialProfile
from src.domain.shared.percentage import Percentage


class CreateProfileUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        currency: str,
        dependents: int,
        monthly_expense_reduction_capacity: Optional[Percentage],
        name: Optional[str] = None,
    ) -> FinancialProfile:
        now = datetime.utcnow()
        profile = FinancialProfile(
            id=str(uuid4()),
            currency=currency,
            dependents=dependents,
            monthly_expense_reduction_capacity=monthly_expense_reduction_capacity,
            created_at=now,
            updated_at=now,
            name=name,
        )
        self._repo.add(profile)
        return profile


class GetProfileUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, profile_id: str) -> Optional[FinancialProfile]:
        return self._repo.get(profile_id)


class UpdateProfileUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, profile: FinancialProfile) -> None:
        profile.updated_at = datetime.utcnow()
        self._repo.update(profile)
