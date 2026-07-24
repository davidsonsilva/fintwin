from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.domain.cashflow.entities import FinancialEvent
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import EventModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(event: FinancialEvent) -> EventModel:
    return EventModel(
        id=event.id,
        profile_id=event.profile_id,
        description=event.description,
        event_type=event.event_type,
        amount_amount=event.amount.amount,
        amount_currency=event.amount.currency,
        date=event.date,
        recurrence=event.recurrence,
        direction=event.direction,
    )


def _to_entity(model: EventModel) -> FinancialEvent:
    return FinancialEvent(
        id=model.id,
        profile_id=model.profile_id,
        description=model.description,
        event_type=model.event_type,
        amount=Money(Decimal(str(model.amount_amount)), model.amount_currency),
        date=model.date,
        recurrence=model.recurrence,
        direction=model.direction,
    )


class SqlAlchemyEventRepository(SqlAlchemyRepository[EventModel, FinancialEvent]):
    model = EventModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
