# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Registro de Recomendações e a superfície de insight do dashboard.

Divisão de responsabilidades nas rotas:

- `GET  /profiles/{id}/insight`             o que o card mostra agora (leitura pura)
- `POST /profiles/{id}/recommendations/detect`  roda o motor e registra
- `GET  /profiles/{id}/recommendations`     o registro completo
- `PATCH /recommendations/{id}/decision`    aprova (cria plano) ou rejeita

Detectar é POST porque escreve. Ler o insight é GET porque o card não pode
criar registro a cada render.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.application.use_cases.recommendation_use_cases import (
    DecideRecommendationUseCase,
    DetectRecommendationUseCase,
    GetInsightUseCase,
    GetRecommendationUseCase,
    ListRecommendationsUseCase,
    RegisterConversationRecommendationUseCase,
)
from src.domain.recommendations.entities import RecommendationStatus
from src.domain.recommendations.lifecycle import (
    InvalidTransitionError,
    StaleRecommendationError,
)
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.preventive_plan_repository import (
    SqlAlchemyPreventivePlanRepository,
)
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from src.interfaces.http.schemas.recommendation import (
    ConversationRecommendationRequest,
    DecisionRequest,
    DetectRequest,
    InsightResponse,
    OpportunityResultResponse,
    RecommendationResponse,
)

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["recommendations"])
recommendations_router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


def _serialize(result) -> dict:
    return OpportunityResultResponse.from_domain(result).to_payload()


def _repos(session: Session) -> dict:
    return {
        "recommendation_repo": SqlAlchemyRecommendationRepository(session),
        "account_repo": SqlAlchemyAccountRepository(session),
        "income_repo": SqlAlchemyIncomeSourceRepository(session),
        "obligation_repo": SqlAlchemyObligationRepository(session),
        "debt_repo": SqlAlchemyDebtRepository(session),
        "goal_repo": SqlAlchemyGoalRepository(session),
        "event_repo": SqlAlchemyEventRepository(session),
        "plan_repo": SqlAlchemyPreventivePlanRepository(session),
    }


def _get_profile_or_404(profile_id: str, session: Session):
    profile = GetProfileUseCase(SqlAlchemyProfileRepository(session)).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


@profiles_router.get("/{profile_id}/insight", response_model=InsightResponse)
def get_insight(profile_id: str, session: Session = Depends(get_session)) -> InsightResponse:
    profile = _get_profile_or_404(profile_id, session)
    surface = GetInsightUseCase(serializer=_serialize, **_repos(session)).execute(
        profile_id, profile.currency
    )
    return InsightResponse.from_domain(surface)


@profiles_router.post("/{profile_id}/recommendations/detect", response_model=InsightResponse)
def detect_recommendation(
    profile_id: str,
    payload: DetectRequest | None = None,
    session: Session = Depends(get_session),
) -> InsightResponse:
    profile = _get_profile_or_404(profile_id, session)
    surface = DetectRecommendationUseCase(serializer=_serialize, **_repos(session)).execute(
        profile_id, profile.currency, custom_pct=payload.custom_pct if payload else None
    )
    return InsightResponse.from_domain(surface)


@profiles_router.get("/{profile_id}/recommendations", response_model=list[RecommendationResponse])
def list_recommendations(
    profile_id: str,
    status: Optional[RecommendationStatus] = Query(default=None),
    session: Session = Depends(get_session),
) -> list[RecommendationResponse]:
    _get_profile_or_404(profile_id, session)
    rows = ListRecommendationsUseCase(SqlAlchemyRecommendationRepository(session)).execute(
        profile_id, status
    )
    return [RecommendationResponse.from_domain(row) for row in rows]


@profiles_router.post(
    "/{profile_id}/recommendations/from-conversation",
    response_model=RecommendationResponse,
    status_code=201,
)
def register_from_conversation(
    profile_id: str,
    payload: ConversationRecommendationRequest,
    session: Session = Depends(get_session),
) -> RecommendationResponse:
    """Só é chamado por um gesto explícito do usuário no chat.

    Nenhuma resposta do agente vira recomendação automaticamente.
    """
    profile = _get_profile_or_404(profile_id, session)
    saved = RegisterConversationRecommendationUseCase(**_repos(session)).execute(
        profile_id=profile_id,
        currency=profile.currency,
        conversation_id=payload.conversation_id,
        message_id=payload.message_id,
        payload=payload.payload,
    )
    return RecommendationResponse.from_domain(saved)


@recommendations_router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(
    recommendation_id: str, session: Session = Depends(get_session)
) -> RecommendationResponse:
    repo = SqlAlchemyRecommendationRepository(session)
    stored = repo.get(recommendation_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Recomendação não encontrada.")

    profile = _get_profile_or_404(stored.profile_id, session)
    surface = GetRecommendationUseCase(**_repos(session)).execute(
        recommendation_id, profile.currency
    )
    return RecommendationResponse.from_domain(surface.recommendation, surface.stale)


@recommendations_router.patch("/{recommendation_id}/decision", response_model=RecommendationResponse)
def decide_recommendation(
    recommendation_id: str,
    payload: DecisionRequest,
    session: Session = Depends(get_session),
) -> RecommendationResponse:
    repo = SqlAlchemyRecommendationRepository(session)
    stored = repo.get(recommendation_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Recomendação não encontrada.")

    profile = _get_profile_or_404(stored.profile_id, session)
    use_case = DecideRecommendationUseCase(**_repos(session))
    try:
        updated = use_case.execute(
            recommendation_id=recommendation_id,
            currency=profile.currency,
            approve=payload.decision == "approved",
            selected_scenario=payload.selected_scenario,
        )
    except StaleRecommendationError as exc:
        # 409, não 400: o pedido está correto, o estado é que mudou.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return RecommendationResponse.from_domain(updated)
