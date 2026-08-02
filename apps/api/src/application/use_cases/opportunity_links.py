# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""O que já endereça um assunto: plano em execução ou recomendação pendente.

Mora fora dos dois casos de uso porque os dois precisam da mesma resposta em
momentos diferentes: quando o bloco é montado (para escolher as ações que a
interface exibe) e de novo quando a pessoa clica (para decidir se aquela ação
ainda vale). Se as duas perguntas tivessem implementações separadas, a segunda
acabaria divergindo da primeira — e é justamente a segunda que autoriza.
"""

from __future__ import annotations

from typing import Any, Optional

from src.domain.agent.topics import AgentTopic
from src.domain.preventive_plans.entities import ACTIVE_PLAN_STATUSES
from src.domain.recommendations.entities import RecommendationKind


def related_plan_id(plan_repo: Any, profile_id: str, topic: AgentTopic) -> Optional[str]:
    """Plano ainda em execução que já endereça este assunto.

    O plano não guarda `subject_key`: o vínculo é por código de risco.
    """
    for plan in plan_repo.list_by_profile(profile_id):
        if plan.risk_code in topic.plan_risk_codes and plan.status in ACTIVE_PLAN_STATUSES:
            return plan.id
    return None


def related_recommendation_id(
    recommendation_repo: Any,
    profile_id: str,
    topic: AgentTopic,
    subject_key: Optional[str] = None,
) -> Optional[str]:
    """Recomendação equivalente aguardando decisão.

    Equivalência é por identidade da oportunidade. O motor identifica a dele
    pelo `kind`; a recomendação nascida da conversa carrega `topic` e
    `subject_key` no payload, porque todas compartilham o mesmo `kind`.
    """
    by_kind = topic.recommendation_kind is not RecommendationKind.CONVERSATION_ADVICE
    for recommendation in recommendation_repo.list_pending(profile_id):
        if by_kind:
            if recommendation.kind is topic.recommendation_kind:
                return recommendation.id
            continue
        payload = recommendation.payload or {}
        if payload.get("topic") == topic.code and payload.get("subject_key") == subject_key:
            return recommendation.id
    return None
