# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Repositório de FinancialProfile: regras próprias (sem delete, um perfil por onboarding)."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.domain.financial_profile.entities import FinancialProfile
from src.domain.shared.percentage import Percentage
from src.infrastructure.persistence.models import ProfileModel


def _to_model(profile: FinancialProfile) -> ProfileModel:
    return ProfileModel(
        id=profile.id,
        currency=profile.currency,
        dependents=profile.dependents,
        monthly_expense_reduction_capacity=(
            profile.monthly_expense_reduction_capacity.as_fraction()
            if profile.monthly_expense_reduction_capacity is not None
            else None
        ),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _to_entity(model: ProfileModel) -> FinancialProfile:
    return FinancialProfile(
        id=model.id,
        currency=model.currency,
        dependents=model.dependents,
        monthly_expense_reduction_capacity=(
            Percentage(Decimal(str(model.monthly_expense_reduction_capacity)))
            if model.monthly_expense_reduction_capacity is not None
            else None
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, profile: FinancialProfile) -> None:
        self._session.add(_to_model(profile))
        self._session.commit()

    def get(self, profile_id: str) -> Optional[FinancialProfile]:
        model = self._session.get(ProfileModel, profile_id)
        return _to_entity(model) if model is not None else None

    def update(self, profile: FinancialProfile) -> None:
        self._session.merge(_to_model(profile))
        self._session.commit()
