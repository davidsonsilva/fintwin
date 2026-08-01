# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Registro de Recomendações — a memória de decisão do FinTwin.

Três papéis distintos, que não devem ser confundidos:

- o **card Insight** mostra o próximo assunto que merece atenção (uma
  recomendação pendente, ou nenhuma);
- o **registro** guarda tudo o que o FinTwin já recomendou, com o desfecho;
- os **planos preventivos** acompanham a execução do que foi aprovado.

Uma recomendação aprovada sai do card e vira plano. Ela não some: fica no
registro, com o cenário que a pessoa escolheu e a análise que ela viu ao
decidir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional


class RecommendationStatus(str, Enum):
    """Ciclo de vida. `pending` é o único estado que aparece no card Insight."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    #: Os dados mudaram e uma nova análise não encontrou nada no lugar.
    EXPIRED = "expired"
    #: Uma análise posterior produziu outra recomendação para o mesmo assunto.
    SUPERSEDED = "superseded"


#: Estados que encerram a recomendação. Nenhuma transição sai daqui.
TERMINAL_STATUSES = frozenset(
    {
        RecommendationStatus.APPROVED,
        RecommendationStatus.REJECTED,
        RecommendationStatus.EXPIRED,
        RecommendationStatus.SUPERSEDED,
    }
)


class RecommendationSource(str, Enum):
    """De onde a recomendação veio.

    `conversation` exige um gesto explícito do usuário no chat ("Salvar como
    recomendação"). Resposta de IA não vira registro sozinha.
    """

    ENGINE = "engine"
    CONVERSATION = "conversation"


class RecommendationKind(str, Enum):
    """Assunto da recomendação — é por ele que uma substitui a outra."""

    GOAL_ACCELERATION = "goal_acceleration"
    CONVERSATION_ADVICE = "conversation_advice"


@dataclass
class Recommendation:
    id: str
    profile_id: str
    kind: RecommendationKind
    source: RecommendationSource
    status: RecommendationStatus
    generated_at: datetime

    #: Snapshot completo da análise. Nunca recalculado: é o que a pessoa viu.
    payload: Mapping[str, Any]
    #: Impressão digital dos dados usados, para detectar defasagem.
    input_fingerprint: str

    scenario: str = "probable"
    decided_at: Optional[datetime] = None
    selected_scenario: Optional[str] = None

    #: Encadeamento de versões. Novos dados não sobrescrevem: criam elo.
    supersedes_id: Optional[str] = None
    superseded_by_id: Optional[str] = None

    #: Plano preventivo criado na aprovação.
    plan_id: Optional[str] = None

    #: Origem quando `source` é `conversation`.
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None

    def is_open(self) -> bool:
        return self.status is RecommendationStatus.PENDING


@dataclass
class InsightSurface:
    """O que o card Insight precisa saber, e nada além disso.

    Ou existe uma recomendação pendente, ou não existe — e nesse caso o card
    diz que as finanças seguem monitoradas. O diagnóstico corrente acompanha
    para o card poder explicar *por que* não há ação.
    """

    recommendation: Optional[Recommendation]
    #: `True` quando os dados mudaram desde que a pendente foi gerada.
    stale: bool = False
    #: Resultado do motor agora, serializado — usado quando não há pendente.
    diagnosis: Optional[Mapping[str, Any]] = None
    assumptions: list[str] = field(default_factory=list)

    #: Plano em execução nascido de uma aprovação anterior.
    #:
    #: Aprovar não movimenta dinheiro, então os dados financeiros continuam os
    #: mesmos e o motor enxergaria a mesma oportunidade para sempre. Enquanto
    #: houver plano ativo para o assunto, ele deixa de ser "próxima ação": já
    #: está endereçado, e quem acompanha a execução são os Planos preventivos.
    #: O card cita o plano em uma linha e segue monitorando — não vira lápide
    #: da recomendação aprovada.
    active_plan_id: Optional[str] = None
