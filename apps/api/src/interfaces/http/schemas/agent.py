# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Schemas HTTP do agente conversacional (Spec seções 18.11 e 19)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping, Optional

from pydantic import BaseModel

from src.application.use_cases.agent_use_cases import AgentReply
from src.domain.agent import opportunities as opportunity_blocks
from src.domain.agent.entities import AgentMessage
from src.domain.agent.opportunities import ActionableOpportunity

_CONTRACT_VERSION = "v1"


class AgentMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class PendingActionSchema(BaseModel):
    action_id: str
    decision_type: str
    parameters: dict[str, Any]
    confirmed: bool = False


class OpportunityAssessmentSchema(BaseModel):
    """Classificação oficial do assunto. Ausente quando o domínio não tem uma."""

    value: Optional[Decimal] = None
    tier: Optional[str] = None
    severity: Optional[str] = None
    policy_id: Optional[str] = None
    policy_version: Optional[str] = None


class ActionableOpportunitySchema(BaseModel):
    """Bloco estruturado independente. O cliente não interpreta Markdown."""

    id: str
    topic: str
    title: str
    diagnosis: str
    suggested_actions: list[str]
    evidence_references: list[str]
    assessment: Optional[OpportunityAssessmentSchema] = None
    requires_simulation: bool
    simulation_status: str
    related_recommendation_id: Optional[str] = None
    related_plan_id: Optional[str] = None
    available_actions: list[str]

    @classmethod
    def from_domain(cls, opportunity: ActionableOpportunity) -> "ActionableOpportunitySchema":
        return cls.model_validate(opportunity_blocks.to_dict(opportunity))

    @classmethod
    def from_stored(cls, data: Mapping[str, Any]) -> "ActionableOpportunitySchema":
        """Bloco já persistido, devolvido como foi gravado — nunca recalculado."""
        return cls.model_validate(dict(data))


class AgentMessageData(BaseModel):
    conversation_id: str
    message_id: str
    reply: str
    tool_calls: list[dict[str, Any]]
    pending_action: Optional[PendingActionSchema]
    components_to_update: list[str]
    pending_questions: list[str]
    opportunities: list[ActionableOpportunitySchema] = []

    @classmethod
    def from_domain(cls, agent_reply: AgentReply) -> "AgentMessageData":
        return cls(
            conversation_id=agent_reply.conversation_id,
            message_id=agent_reply.message_id,
            reply=agent_reply.reply,
            tool_calls=list(agent_reply.tool_calls),
            pending_action=(
                PendingActionSchema(**agent_reply.pending_action) if agent_reply.pending_action is not None else None
            ),
            components_to_update=list(agent_reply.components_to_update),
            pending_questions=list(agent_reply.pending_questions),
            opportunities=[
                ActionableOpportunitySchema.from_domain(item) for item in agent_reply.opportunities
            ],
        )


class AgentMessageResponse(BaseModel):
    data: AgentMessageData
    evidence: list[dict[str, Any]]
    assumptions: list[str]
    limitations: list[str]
    generated_at: datetime
    version: str = _CONTRACT_VERSION

    @classmethod
    def from_domain(cls, agent_reply: AgentReply) -> "AgentMessageResponse":
        return cls(
            data=AgentMessageData.from_domain(agent_reply),
            evidence=list(agent_reply.evidence),
            assumptions=list(agent_reply.assumptions),
            limitations=list(agent_reply.limitations),
            generated_at=datetime.now(timezone.utc),
        )


class AgentMessageHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    tool_calls: list[dict[str, Any]]
    pending_action: Optional[PendingActionSchema]
    opportunities: list[ActionableOpportunitySchema] = []
    created_at: datetime

    @classmethod
    def from_domain(cls, message: AgentMessage) -> "AgentMessageHistoryItem":
        return cls(
            id=message.id,
            role=message.role.value,
            content=message.content,
            tool_calls=list(message.tool_calls),
            pending_action=(
                PendingActionSchema(
                    **{k: v for k, v in message.pending_action.items() if k != "confirmed"},
                    confirmed=message.confirmed,
                )
                if message.pending_action is not None
                else None
            ),
            opportunities=[ActionableOpportunitySchema.from_stored(item) for item in message.opportunities],
            created_at=message.created_at,
        )
