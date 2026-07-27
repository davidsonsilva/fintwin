# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.agent_use_cases import (
    ConfirmPendingActionUseCase,
    PendingActionAlreadyConfirmedError,
    PendingActionNotFoundError,
    SendAgentMessageUseCase,
)
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.application.use_cases.simulation_use_cases import SimulateDecisionUseCase
from src.domain.decisions.validation import InvalidDecisionParametersError
from src.infrastructure.llm.anthropic_client import AnthropicAgentClient
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.agent_message_repository import SqlAlchemyAgentMessageRepository
from src.infrastructure.repositories.conversation_repository import SqlAlchemyConversationRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.fragility_repository import SqlAlchemyFragilityRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.simulation_repository import SqlAlchemySimulationRepository
from src.interfaces.http.rate_limit import agent_message_rate_limiter
from src.interfaces.http.schemas.agent import AgentMessageHistoryItem, AgentMessageRequest, AgentMessageResponse
from src.interfaces.http.schemas.simulation import SimulationResponse

router = APIRouter(prefix="/api/v1/profiles", tags=["agent"])

_llm_client_singleton = AnthropicAgentClient()


def get_llm_client() -> AnthropicAgentClient:
    return _llm_client_singleton


def _get_profile_or_404(profile_id: str, session: Session):
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(profile_repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


def _build_send_message_use_case(session: Session, llm_client) -> SendAgentMessageUseCase:
    return SendAgentMessageUseCase(
        llm_client=llm_client,
        conversation_repo=SqlAlchemyConversationRepository(session),
        agent_message_repo=SqlAlchemyAgentMessageRepository(session),
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        fragility_repo=SqlAlchemyFragilityRepository(session),
    )


@router.post(
    "/{profile_id}/agent/messages",
    response_model=AgentMessageResponse,
    status_code=201,
    dependencies=[Depends(agent_message_rate_limiter)],
)
def send_agent_message(
    profile_id: str,
    payload: AgentMessageRequest,
    session: Session = Depends(get_session),
    llm_client=Depends(get_llm_client),
) -> AgentMessageResponse:
    profile = _get_profile_or_404(profile_id, session)

    use_case = _build_send_message_use_case(session, llm_client)
    try:
        reply = use_case.execute(
            profile_id=profile_id,
            currency=profile.currency,
            conversation_id=payload.conversation_id,
            message=payload.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AgentMessageResponse.from_domain(reply)


@router.post("/{profile_id}/agent/actions/{action_id}/confirm", response_model=SimulationResponse, status_code=201)
def confirm_agent_action(
    profile_id: str, action_id: str, session: Session = Depends(get_session)
) -> SimulationResponse:
    profile = _get_profile_or_404(profile_id, session)

    simulate_use_case = SimulateDecisionUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        simulation_repo=SqlAlchemySimulationRepository(session),
    )
    confirm_use_case = ConfirmPendingActionUseCase(
        agent_message_repo=SqlAlchemyAgentMessageRepository(session),
        conversation_repo=SqlAlchemyConversationRepository(session),
        simulate_decision_use_case=simulate_use_case,
    )
    try:
        simulation = confirm_use_case.execute(profile_id=profile_id, action_id=action_id, currency=profile.currency)
    except PendingActionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PendingActionAlreadyConfirmedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidDecisionParametersError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SimulationResponse.from_domain(simulation)


@router.get(
    "/{profile_id}/agent/conversations/{conversation_id}/messages",
    response_model=list[AgentMessageHistoryItem],
)
def list_agent_messages(
    profile_id: str, conversation_id: str, session: Session = Depends(get_session)
) -> list[AgentMessageHistoryItem]:
    _get_profile_or_404(profile_id, session)
    conversation_repo = SqlAlchemyConversationRepository(session)
    conversation = conversation_repo.get(conversation_id)
    if conversation is None or conversation.profile_id != profile_id:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    messages = SqlAlchemyAgentMessageRepository(session).list_by_conversation(conversation_id)
    return [AgentMessageHistoryItem.from_domain(message) for message in messages]
