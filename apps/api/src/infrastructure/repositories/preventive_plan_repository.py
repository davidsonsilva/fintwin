from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.preventive_plans.entities import PreventivePlan
from src.infrastructure.persistence.models import PreventivePlanModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(plan: PreventivePlan) -> PreventivePlanModel:
    return PreventivePlanModel(
        id=plan.id,
        profile_id=plan.profile_id,
        risk_code=plan.risk_code,
        status=plan.status,
        actions=list(plan.actions),
        expected_result=dict(plan.expected_result),
        created_at=plan.created_at,
        approved_at=plan.approved_at,
    )


def _to_entity(model: PreventivePlanModel) -> PreventivePlan:
    return PreventivePlan(
        id=model.id,
        profile_id=model.profile_id,
        risk_code=model.risk_code,
        status=model.status,
        actions=list(model.actions),
        expected_result=dict(model.expected_result),
        created_at=model.created_at,
        approved_at=model.approved_at,
    )


class SqlAlchemyPreventivePlanRepository(SqlAlchemyRepository[PreventivePlanModel, PreventivePlan]):
    model = PreventivePlanModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)
