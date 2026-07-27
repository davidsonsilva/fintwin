# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.domain.obligations.entities import Debt
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import DebtModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(debt: Debt) -> DebtModel:
    return DebtModel(
        id=debt.id,
        profile_id=debt.profile_id,
        description=debt.description,
        outstanding_balance_amount=debt.outstanding_balance.amount,
        outstanding_balance_currency=debt.outstanding_balance.currency,
        installment_amount_amount=debt.installment_amount.amount,
        installment_amount_currency=debt.installment_amount.currency,
        remaining_installments=debt.remaining_installments,
        interest_rate_optional=debt.interest_rate_optional,
        due_day=debt.due_day,
    )


def _to_entity(model: DebtModel) -> Debt:
    return Debt(
        id=model.id,
        profile_id=model.profile_id,
        description=model.description,
        outstanding_balance=Money(
            Decimal(str(model.outstanding_balance_amount)), model.outstanding_balance_currency
        ),
        installment_amount=Money(
            Decimal(str(model.installment_amount_amount)), model.installment_amount_currency
        ),
        remaining_installments=model.remaining_installments,
        interest_rate_optional=model.interest_rate_optional,
        due_day=model.due_day,
    )


class SqlAlchemyDebtRepository(SqlAlchemyRepository[DebtModel, Debt]):
    model = DebtModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
