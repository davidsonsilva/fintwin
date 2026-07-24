from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.domain.obligations.entities import FinancialObligation
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import ObligationModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(obligation: FinancialObligation) -> ObligationModel:
    return ObligationModel(
        id=obligation.id,
        profile_id=obligation.profile_id,
        description=obligation.description,
        amount_amount=obligation.amount.amount,
        amount_currency=obligation.amount.currency,
        category=obligation.category,
        frequency=obligation.frequency,
        due_day=obligation.due_day,
        start_date=obligation.start_date,
        end_date=obligation.end_date,
        essential=obligation.essential,
        debt_related=obligation.debt_related,
    )


def _to_entity(model: ObligationModel) -> FinancialObligation:
    return FinancialObligation(
        id=model.id,
        profile_id=model.profile_id,
        description=model.description,
        amount=Money(Decimal(str(model.amount_amount)), model.amount_currency),
        category=model.category,
        frequency=model.frequency,
        due_day=model.due_day,
        start_date=model.start_date,
        end_date=model.end_date,
        essential=model.essential,
        debt_related=model.debt_related,
    )


class SqlAlchemyObligationRepository(SqlAlchemyRepository[ObligationModel, FinancialObligation]):
    model = ObligationModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
