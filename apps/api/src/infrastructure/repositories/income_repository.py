# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.domain.obligations.entities import IncomeSource
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import IncomeSourceModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(income: IncomeSource) -> IncomeSourceModel:
    return IncomeSourceModel(
        id=income.id,
        profile_id=income.profile_id,
        description=income.description,
        amount_amount=income.amount.amount,
        amount_currency=income.amount.currency,
        frequency=income.frequency,
        start_date=income.start_date,
        end_date=income.end_date,
        stability=income.stability,
    )


def _to_entity(model: IncomeSourceModel) -> IncomeSource:
    return IncomeSource(
        id=model.id,
        profile_id=model.profile_id,
        description=model.description,
        amount=Money(Decimal(str(model.amount_amount)), model.amount_currency),
        frequency=model.frequency,
        start_date=model.start_date,
        end_date=model.end_date,
        stability=model.stability,
    )


class SqlAlchemyIncomeSourceRepository(SqlAlchemyRepository[IncomeSourceModel, IncomeSource]):
    model = IncomeSourceModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
