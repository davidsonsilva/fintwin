# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Catálogo de assuntos que o agente pode levantar como oportunidade.

Uma oportunidade não é texto livre: é um assunto que o FinTwin já sabe
endereçar. O catálogo responde, por assunto, o que o backend decide sozinho —
nunca a IA:

- existe motor capaz de simular este assunto? (`decision_type`)
- que plano preventivo já o endereça? (`plan_risk_codes`)
- de onde sai a classificação oficial, quando ela existe? (`assessment`)
- que entidade o assunto pode apontar? (`subject_kind`)

Assunto fora do catálogo não vira bloco estruturado: continua sendo conversa.
Isso é deliberado — um bloco com botão de ação promete uma capacidade, e o
produto só pode prometer o que o domínio sustenta.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.domain.recommendations.entities import RecommendationKind


class SubjectKind(str, Enum):
    """Tipo de entidade que um assunto pode apontar em `subject_key`.

    Existe porque "assunto" sozinho é amplo demais: duas dívidas diferentes são
    duas oportunidades diferentes, não uma repetição. A chave completa é
    `topic + subject_key`; quando o assunto não tem entidade específica (a
    reserva de emergência é uma só), a identidade é só o `topic`.
    """

    GOAL = "goal"
    DEBT = "debt"
    INCOME_SOURCE = "source"


class AssessmentSource(str, Enum):
    """De onde vem a classificação oficial do assunto."""

    #: Faixas de comprometimento da renda (`src.domain.shared.indicators`).
    INCOME_COMMITMENT = "income_commitment"
    #: Severidade atribuída pelo Radar de Fragilidade.
    FRAGILITY_FINDING = "fragility_finding"


@dataclass(frozen=True)
class AgentTopic:
    code: str
    label: str
    #: Tipo de decisão simulável. `None` = não há motor para este assunto.
    decision_type: Optional[str] = None
    #: Códigos de plano preventivo que endereçam o assunto.
    plan_risk_codes: tuple[str, ...] = ()
    #: Códigos de fragilidade que classificam o assunto.
    fragility_codes: tuple[str, ...] = ()
    assessment: Optional[AssessmentSource] = None
    #: Assunto correspondente no registro de recomendações.
    recommendation_kind: RecommendationKind = RecommendationKind.CONVERSATION_ADVICE
    #: Entidade que refina a identidade do assunto. `None` = assunto único no
    #: perfil, identificado só pelo `code`.
    subject_kind: Optional[SubjectKind] = None

    @property
    def requires_simulation(self) -> bool:
        """Só é simulável o assunto com motor de decisão correspondente."""
        return self.decision_type is not None


AGENT_TOPICS: dict[str, AgentTopic] = {
    "goal_acceleration": AgentTopic(
        code="goal_acceleration",
        label="Aceleração da meta principal",
        # O motor de oportunidade já calcula os cenários deste assunto; não há
        # decisão do simulador que o represente.
        plan_risk_codes=("GOAL_ACCELERATION_OPPORTUNITY",),
        recommendation_kind=RecommendationKind.GOAL_ACCELERATION,
        subject_kind=SubjectKind.GOAL,
    ),
    "emergency_reserve": AgentTopic(
        code="emergency_reserve",
        label="Reserva de emergência",
        decision_type="RESERVE_INCREASE",
        plan_risk_codes=("RESERVE_BELOW_THREE_MONTHS", "PROJECTED_RESERVE_DECLINE"),
        fragility_codes=("RESERVE_BELOW_THREE_MONTHS", "PROJECTED_RESERVE_DECLINE"),
        assessment=AssessmentSource.FRAGILITY_FINDING,
    ),
    "income_commitment": AgentTopic(
        code="income_commitment",
        label="Comprometimento da renda",
        plan_risk_codes=("ESSENTIAL_EXPENSE_RATIO",),
        assessment=AssessmentSource.INCOME_COMMITMENT,
    ),
    "income_concentration": AgentTopic(
        code="income_concentration",
        label="Concentração da renda",
        decision_type="INCOME_LOSS",
        plan_risk_codes=("INCOME_CONCENTRATION",),
        fragility_codes=("INCOME_CONCENTRATION",),
        assessment=AssessmentSource.FRAGILITY_FINDING,
        subject_kind=SubjectKind.INCOME_SOURCE,
    ),
    "debt_service": AgentTopic(
        code="debt_service",
        label="Serviço da dívida",
        plan_risk_codes=("DEBT_SERVICE_RATIO",),
        fragility_codes=("DEBT_SERVICE_RATIO",),
        assessment=AssessmentSource.FRAGILITY_FINDING,
        subject_kind=SubjectKind.DEBT,
    ),
    "annual_expense_provision": AgentTopic(
        code="annual_expense_provision",
        label="Provisão de despesa anual",
        decision_type="NEW_RECURRING_EXPENSE",
        plan_risk_codes=("UNPROVISIONED_ANNUAL_EXPENSE",),
        fragility_codes=("UNPROVISIONED_ANNUAL_EXPENSE",),
        assessment=AssessmentSource.FRAGILITY_FINDING,
    ),
    "due_date_concentration": AgentTopic(
        code="due_date_concentration",
        label="Vencimentos concentrados",
        # Não há decisão simulável: reorganizar datas não é uma decisão que o
        # motor saiba aplicar. O assunto é diagnóstico e plano, não simulação.
        plan_risk_codes=("CONCENTRATED_DUE_DATES",),
        fragility_codes=("CONCENTRATED_DUE_DATES",),
        assessment=AssessmentSource.FRAGILITY_FINDING,
    ),
    "projected_deficit": AgentTopic(
        code="projected_deficit",
        label="Déficit projetado",
        plan_risk_codes=("PROJECTED_DEFICIT_90_DAYS",),
        fragility_codes=("PROJECTED_DEFICIT_90_DAYS",),
        assessment=AssessmentSource.FRAGILITY_FINDING,
    ),
}


TOPIC_CODES: tuple[str, ...] = tuple(AGENT_TOPICS)


def get_topic(code: str) -> Optional[AgentTopic]:
    return AGENT_TOPICS.get(code)
