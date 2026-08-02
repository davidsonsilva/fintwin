# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Oportunidade acionável: o bloco estruturado que uma resposta pode conter.

Uma resposta da IA pode conter várias oportunidades. Cada uma sai como um bloco
independente, com identidade, evidências e ações próprias — a interface não lê
Markdown nem procura trechos como "O que fazer".

A divisão de responsabilidade é rígida:

- a IA descreve (título, diagnóstico, o que fazer) e aponta as evidências que
  usou;
- o backend classifica (`assessment`), decide o que é simulável e quais ações a
  pessoa pode tomar (`available_actions`).

Por isso `assessment` é opcional: quando o domínio não tem classificação
oficial para o assunto, o bloco sai sem nenhuma — nunca com uma inventada.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from src.domain.agent.topics import AgentTopic


class SimulationStatus(str, Enum):
    """Estado do cálculo — separado do ciclo de vida da recomendação.

    Uma oportunidade pode estar simulada e ainda assim não ter virado
    recomendação, e vice-versa. Misturar os dois faria o card mentir sobre um
    dos dois estados.
    """

    NOT_SIMULATED = "not_simulated"
    SIMULATED = "simulated"
    NOT_REQUIRED = "not_required"


class OpportunityAction(str, Enum):
    SIMULATE = "simulate"
    SAVE = "save"
    VIEW_RECOMMENDATION = "view_recommendation"
    VIEW_PLAN = "view_plan"


@dataclass(frozen=True)
class OpportunityAssessment:
    """Classificação oficial do assunto. Só existe se o domínio produziu uma."""

    value: Optional[Decimal] = None
    tier: Optional[str] = None
    severity: Optional[str] = None
    policy_id: Optional[str] = None
    policy_version: Optional[str] = None


@dataclass(frozen=True)
class ActionableOpportunity:
    id: str
    topic: str
    title: str
    diagnosis: str
    suggested_actions: tuple[str, ...]
    evidence_references: tuple[str, ...]
    requires_simulation: bool
    simulation_status: SimulationStatus
    available_actions: tuple[OpportunityAction, ...]
    assessment: Optional[OpportunityAssessment] = None
    #: Entidade específica do assunto ("goal:123"). `None` = assunto único.
    subject_key: Optional[str] = None
    related_recommendation_id: Optional[str] = None
    related_plan_id: Optional[str] = None

    @property
    def identity(self) -> tuple[str, Optional[str]]:
        """O que faz duas oportunidades serem a mesma. Ver `identity_of`."""
        return (self.topic, self.subject_key)


def identity_of(topic_code: str, subject_key: Optional[str]) -> tuple[str, Optional[str]]:
    """Identidade de uma oportunidade: assunto mais a entidade que ela aponta.

    Só o assunto seria amplo demais — duas dívidas diferentes viram um bloco
    só, e a pessoa perde uma delas. Quando o assunto não tem entidade própria,
    a identidade é só o assunto.
    """
    return (topic_code, subject_key)


def available_actions(
    topic: AgentTopic,
    related_plan_id: Optional[str],
    related_recommendation_id: Optional[str],
) -> tuple[OpportunityAction, ...]:
    """As ações que o backend oferece — a IA não opina sobre isto.

    `simulate` só aparece quando existe motor capaz de simular o assunto.
    Salvar é o caminho de quem ainda não registrou nada: se o assunto já virou
    plano em execução, ou já tem recomendação aguardando decisão, a ação é ver
    o que existe, não criar uma segunda cópia do mesmo assunto. O plano vence a
    recomendação porque é o estado mais avançado dos dois.
    """
    actions: list[OpportunityAction] = []
    if topic.requires_simulation:
        actions.append(OpportunityAction.SIMULATE)
    if related_plan_id is not None:
        actions.append(OpportunityAction.VIEW_PLAN)
    elif related_recommendation_id is not None:
        actions.append(OpportunityAction.VIEW_RECOMMENDATION)
    else:
        actions.append(OpportunityAction.SAVE)
    return tuple(actions)


def build_opportunity(
    opportunity_id: str,
    topic: AgentTopic,
    title: str,
    diagnosis: str,
    suggested_actions: Sequence[str],
    evidence_references: Sequence[str],
    assessment: Optional[OpportunityAssessment],
    related_plan_id: Optional[str],
    related_recommendation_id: Optional[str],
    subject_key: Optional[str] = None,
) -> ActionableOpportunity:
    return ActionableOpportunity(
        id=opportunity_id,
        topic=topic.code,
        subject_key=subject_key,
        title=title,
        diagnosis=diagnosis,
        suggested_actions=tuple(suggested_actions),
        evidence_references=tuple(evidence_references),
        assessment=assessment,
        requires_simulation=topic.requires_simulation,
        # `simulated` é estado de um cálculo que já aconteceu; nada nesta etapa
        # vincula uma simulação existente a uma oportunidade.
        simulation_status=(
            SimulationStatus.NOT_SIMULATED if topic.requires_simulation else SimulationStatus.NOT_REQUIRED
        ),
        related_recommendation_id=related_recommendation_id,
        related_plan_id=related_plan_id,
        available_actions=available_actions(topic, related_plan_id, related_recommendation_id),
    )


def to_dict(opportunity: ActionableOpportunity) -> dict[str, Any]:
    """Forma persistida/transportada. `Decimal` sai como string, como no resto do projeto."""
    assessment = opportunity.assessment
    return {
        "id": opportunity.id,
        "topic": opportunity.topic,
        "subject_key": opportunity.subject_key,
        "title": opportunity.title,
        "diagnosis": opportunity.diagnosis,
        "suggested_actions": list(opportunity.suggested_actions),
        "evidence_references": list(opportunity.evidence_references),
        "assessment": (
            {
                "value": str(assessment.value) if assessment.value is not None else None,
                "tier": assessment.tier,
                "severity": assessment.severity,
                "policy_id": assessment.policy_id,
                "policy_version": assessment.policy_version,
            }
            if assessment is not None
            else None
        ),
        "requires_simulation": opportunity.requires_simulation,
        "simulation_status": opportunity.simulation_status.value,
        "related_recommendation_id": opportunity.related_recommendation_id,
        "related_plan_id": opportunity.related_plan_id,
        "available_actions": [action.value for action in opportunity.available_actions],
    }


def from_dict(data: Mapping[str, Any]) -> ActionableOpportunity:
    raw_assessment = data.get("assessment")
    return ActionableOpportunity(
        id=data["id"],
        topic=data["topic"],
        # Bloco gravado antes de `subject_key` existir: identidade só por assunto.
        subject_key=data.get("subject_key"),
        title=data["title"],
        diagnosis=data["diagnosis"],
        suggested_actions=tuple(data.get("suggested_actions") or ()),
        evidence_references=tuple(data.get("evidence_references") or ()),
        assessment=(
            OpportunityAssessment(
                value=(
                    Decimal(str(raw_assessment["value"])) if raw_assessment.get("value") is not None else None
                ),
                tier=raw_assessment.get("tier"),
                severity=raw_assessment.get("severity"),
                policy_id=raw_assessment.get("policy_id"),
                policy_version=raw_assessment.get("policy_version"),
            )
            if raw_assessment
            else None
        ),
        requires_simulation=bool(data["requires_simulation"]),
        simulation_status=SimulationStatus(data["simulation_status"]),
        related_recommendation_id=data.get("related_recommendation_id"),
        related_plan_id=data.get("related_plan_id"),
        available_actions=tuple(OpportunityAction(action) for action in data.get("available_actions") or ()),
    )
