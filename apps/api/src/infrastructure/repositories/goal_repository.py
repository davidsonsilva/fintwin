from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.domain.decisions.entities import FinancialGoal
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import GoalModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(goal: FinancialGoal) -> GoalModel:
    return GoalModel(
        id=goal.id,
        profile_id=goal.profile_id,
        description=goal.description,
        target_amount_amount=goal.target_amount.amount,
        target_amount_currency=goal.target_amount.currency,
        current_amount_amount=goal.current_amount.amount,
        current_amount_currency=goal.current_amount.currency,
        deadline=goal.deadline,
        priority=goal.priority,
        monthly_contribution_amount=goal.monthly_contribution.amount,
        monthly_contribution_currency=goal.monthly_contribution.currency,
    )


def _to_entity(model: GoalModel) -> FinancialGoal:
    return FinancialGoal(
        id=model.id,
        profile_id=model.profile_id,
        description=model.description,
        target_amount=Money(Decimal(str(model.target_amount_amount)), model.target_amount_currency),
        current_amount=Money(Decimal(str(model.current_amount_amount)), model.current_amount_currency),
        deadline=model.deadline,
        priority=model.priority,
        monthly_contribution=Money(
            Decimal(str(model.monthly_contribution_amount)), model.monthly_contribution_currency
        ),
    )


class SqlAlchemyGoalRepository(SqlAlchemyRepository[GoalModel, FinancialGoal]):
    model = GoalModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
