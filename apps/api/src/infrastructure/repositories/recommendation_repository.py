# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.recommendations.entities import (
    Recommendation,
    RecommendationKind,
    RecommendationSource,
    RecommendationStatus,
)
from src.infrastructure.persistence.models import RecommendationModel

_FIELDS = (
    "kind",
    "source",
    "status",
    "generated_at",
    "scenario",
    "input_fingerprint",
    "payload",
    "decided_at",
    "selected_scenario",
    "supersedes_id",
    "superseded_by_id",
    "plan_id",
    "conversation_id",
    "message_id",
    "opportunity_id",
)


def _to_entity(model: RecommendationModel) -> Recommendation:
    return Recommendation(
        id=model.id,
        profile_id=model.profile_id,
        kind=RecommendationKind(model.kind),
        source=RecommendationSource(model.source),
        status=RecommendationStatus(model.status),
        generated_at=model.generated_at,
        payload=dict(model.payload),
        input_fingerprint=model.input_fingerprint,
        scenario=model.scenario,
        decided_at=model.decided_at,
        selected_scenario=model.selected_scenario,
        supersedes_id=model.supersedes_id,
        superseded_by_id=model.superseded_by_id,
        plan_id=model.plan_id,
        conversation_id=model.conversation_id,
        message_id=model.message_id,
        opportunity_id=model.opportunity_id,
    )


class SqlAlchemyRecommendationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, recommendation: Recommendation) -> Recommendation:
        model = RecommendationModel(
            id=recommendation.id,
            profile_id=recommendation.profile_id,
            kind=recommendation.kind.value,
            source=recommendation.source.value,
            status=recommendation.status.value,
            generated_at=recommendation.generated_at,
            scenario=recommendation.scenario,
            input_fingerprint=recommendation.input_fingerprint,
            payload=dict(recommendation.payload),
            decided_at=recommendation.decided_at,
            selected_scenario=recommendation.selected_scenario,
            supersedes_id=recommendation.supersedes_id,
            superseded_by_id=recommendation.superseded_by_id,
            plan_id=recommendation.plan_id,
            conversation_id=recommendation.conversation_id,
            message_id=recommendation.message_id,
            opportunity_id=recommendation.opportunity_id,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def add_for_opportunity(self, recommendation: Recommendation) -> Recommendation:
        """Insere disputando a unicidade da oportunidade no banco.

        Devolve o que ficou gravado — que pode ser o registro de outra
        requisição, se ela chegou primeiro. Cabe a quem chama comparar o id e
        tratar a corrida perdida.
        """
        try:
            return self.add(recommendation)
        except IntegrityError:
            self._session.rollback()
            # Só engolimos o erro se for de fato a corrida esperada. Qualquer
            # outra causa (FK para um perfil excluído, por exemplo) sobe —
            # inspecionar a mensagem do driver seria específico de banco, então
            # revalidamos consultando o estado real.
            existing = self.get_by_opportunity_id(recommendation.opportunity_id)
            if existing is None:
                raise
            return existing

    def get_by_opportunity_id(self, opportunity_id: Optional[str]) -> Optional[Recommendation]:
        if opportunity_id is None:
            return None
        stmt = select(RecommendationModel).where(
            RecommendationModel.opportunity_id == opportunity_id
        )
        model = self._session.execute(stmt).scalars().first()
        return _to_entity(model) if model is not None else None

    def save(self, recommendation: Recommendation) -> Recommendation:
        """Persiste uma transição já validada pelo domínio."""
        model = self._session.get(RecommendationModel, recommendation.id)
        if model is None:
            raise ValueError(f"Recomendação {recommendation.id} não encontrada.")
        for field in _FIELDS:
            value = getattr(recommendation, field)
            setattr(model, field, value.value if hasattr(value, "value") else value)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get(self, recommendation_id: str) -> Optional[Recommendation]:
        model = self._session.get(RecommendationModel, recommendation_id)
        return _to_entity(model) if model is not None else None

    def get_pending(self, profile_id: str, kind: RecommendationKind) -> Optional[Recommendation]:
        """A pendente mais nova do assunto — é ela que o card Insight mostra."""
        stmt = (
            select(RecommendationModel)
            .where(
                RecommendationModel.profile_id == profile_id,
                RecommendationModel.kind == kind.value,
                RecommendationModel.status == RecommendationStatus.PENDING.value,
            )
            .order_by(RecommendationModel.generated_at.desc())
        )
        model = self._session.execute(stmt).scalars().first()
        return _to_entity(model) if model is not None else None

    def list_approved(self, profile_id: str, kind: RecommendationKind) -> list[Recommendation]:
        """Aprovadas do assunto, da mais nova para a mais antiga."""
        stmt = (
            select(RecommendationModel)
            .where(
                RecommendationModel.profile_id == profile_id,
                RecommendationModel.kind == kind.value,
                RecommendationModel.status == RecommendationStatus.APPROVED.value,
            )
            .order_by(RecommendationModel.generated_at.desc())
        )
        return [_to_entity(m) for m in self._session.execute(stmt).scalars().all()]

    def list_pending(self, profile_id: str) -> list[Recommendation]:
        stmt = (
            select(RecommendationModel)
            .where(
                RecommendationModel.profile_id == profile_id,
                RecommendationModel.status == RecommendationStatus.PENDING.value,
            )
            .order_by(RecommendationModel.generated_at.desc())
        )
        return [_to_entity(m) for m in self._session.execute(stmt).scalars().all()]

    def list_by_profile(
        self, profile_id: str, status: Optional[RecommendationStatus] = None
    ) -> list[Recommendation]:
        stmt = select(RecommendationModel).where(RecommendationModel.profile_id == profile_id)
        if status is not None:
            stmt = stmt.where(RecommendationModel.status == status.value)
        stmt = stmt.order_by(RecommendationModel.generated_at.desc())
        return [_to_entity(m) for m in self._session.execute(stmt).scalars().all()]
