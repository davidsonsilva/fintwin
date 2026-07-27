# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.domain.financial_profile.entities import FinancialAccount
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import AccountModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(account: FinancialAccount) -> AccountModel:
    return AccountModel(
        id=account.id,
        profile_id=account.profile_id,
        description=account.description,
        balance_amount=account.balance.amount,
        balance_currency=account.balance.currency,
        liquidity_type=account.liquidity_type,
        eligible_for_autonomy=account.eligible_for_autonomy,
    )


def _to_entity(model: AccountModel) -> FinancialAccount:
    return FinancialAccount(
        id=model.id,
        profile_id=model.profile_id,
        description=model.description,
        balance=Money(Decimal(str(model.balance_amount)), model.balance_currency),
        liquidity_type=model.liquidity_type,
        eligible_for_autonomy=model.eligible_for_autonomy,
    )


class SqlAlchemyAccountRepository(SqlAlchemyRepository[AccountModel, FinancialAccount]):
    model = AccountModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
