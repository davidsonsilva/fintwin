# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Recomendação financeira proativa: gerar, abrir e decidir.

Gerar é POST porque cria um registro; abrir é GET porque não muda nada. Essa
separação é o que permite a tela ser aberta, fechada e reaberta mostrando
sempre os mesmos números.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.opportunity_use_cases import (
    CreateOpportunityAnalysisUseCase,
    DecideOpportunityAnalysisUseCase,
    GetOpportunityAnalysisUseCase,
    LoadedAnalysis,
)
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.domain.opportunity.entities import AnalysisDecision
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.opportunity_repository import (
    SqlAlchemyOpportunityAnalysisRepository,
)
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.interfaces.http.schemas.opportunity import (
    OpportunityAnalysisRequest,
    OpportunityAnalysisResponse,
    OpportunityDecisionRequest,
    OpportunityResultResponse,
)

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["opportunity"])
analyses_router = APIRouter(prefix="/api/v1/opportunity-analyses", tags=["opportunity"])


def _repos(session: Session) -> dict:
    return {
        "account_repo": SqlAlchemyAccountRepository(session),
        "income_repo": SqlAlchemyIncomeSourceRepository(session),
        "obligation_repo": SqlAlchemyObligationRepository(session),
        "debt_repo": SqlAlchemyDebtRepository(session),
        "goal_repo": SqlAlchemyGoalRepository(session),
        "event_repo": SqlAlchemyEventRepository(session),
    }


def _get_profile_or_404(profile_id: str, session: Session):
    profile = GetProfileUseCase(SqlAlchemyProfileRepository(session)).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


@profiles_router.post("/{profile_id}/opportunity-analyses", response_model=OpportunityAnalysisResponse)
def create_opportunity_analysis(
    profile_id: str,
    payload: OpportunityAnalysisRequest | None = None,
    session: Session = Depends(get_session),
) -> OpportunityAnalysisResponse:
    profile = _get_profile_or_404(profile_id, session)

    use_case = CreateOpportunityAnalysisUseCase(
        analysis_repo=SqlAlchemyOpportunityAnalysisRepository(session),
        serializer=lambda result: OpportunityResultResponse.from_domain(result).to_payload(),
        **_repos(session),
    )
    loaded = use_case.execute(
        profile_id,
        profile.currency,
        custom_pct=payload.custom_pct if payload else None,
    )
    return OpportunityAnalysisResponse.from_domain(loaded)


@profiles_router.get(
    "/{profile_id}/opportunity-analyses/latest",
    response_model=Optional[OpportunityAnalysisResponse],
)
def get_latest_opportunity_analysis(
    profile_id: str, session: Session = Depends(get_session)
) -> Optional[OpportunityAnalysisResponse]:
    """Resumo do card no dashboard, sem criar registro.

    Devolve `null` quando o perfil nunca foi analisado — é o estado inicial do
    card, não um erro.
    """
    profile = _get_profile_or_404(profile_id, session)

    repo = SqlAlchemyOpportunityAnalysisRepository(session)
    latest = repo.get_latest_for_profile(profile_id)
    if latest is None:
        return None

    use_case = GetOpportunityAnalysisUseCase(analysis_repo=repo, **_repos(session))
    return OpportunityAnalysisResponse.from_domain(use_case.execute(latest.id, profile.currency))


@analyses_router.get("/{analysis_id}", response_model=OpportunityAnalysisResponse)
def get_opportunity_analysis(
    analysis_id: str, session: Session = Depends(get_session)
) -> OpportunityAnalysisResponse:
    repo = SqlAlchemyOpportunityAnalysisRepository(session)
    stored = repo.get(analysis_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")

    profile = _get_profile_or_404(stored.profile_id, session)
    use_case = GetOpportunityAnalysisUseCase(analysis_repo=repo, **_repos(session))
    loaded = use_case.execute(analysis_id, profile.currency)
    return OpportunityAnalysisResponse.from_domain(loaded)


@analyses_router.patch("/{analysis_id}/decision", response_model=OpportunityAnalysisResponse)
def decide_opportunity_analysis(
    analysis_id: str,
    payload: OpportunityDecisionRequest,
    session: Session = Depends(get_session),
) -> OpportunityAnalysisResponse:
    repo = SqlAlchemyOpportunityAnalysisRepository(session)
    updated = DecideOpportunityAnalysisUseCase(repo).execute(
        analysis_id=analysis_id,
        decision=AnalysisDecision(payload.decision),
        selected_scenario=payload.selected_scenario,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")

    # A decisão não altera os dados financeiros, então o frescor da análise é
    # o mesmo de antes — recalculado aqui só para a resposta ficar completa.
    profile = _get_profile_or_404(updated.profile_id, session)
    loaded: LoadedAnalysis = GetOpportunityAnalysisUseCase(
        analysis_repo=repo, **_repos(session)
    ).execute(analysis_id, profile.currency)
    return OpportunityAnalysisResponse.from_domain(loaded)
