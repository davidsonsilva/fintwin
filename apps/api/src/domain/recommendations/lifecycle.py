# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Regras de transição do registro de recomendações, puras e testáveis.

Nada aqui toca banco ou HTTP. O que este módulo garante:

- só uma recomendação pendente por assunto (`kind`) e perfil;
- uma recomendação decidida nunca volta atrás;
- aprovar exige que os dados ainda sejam os mesmos que geraram a análise —
  senão a pessoa estaria aprovando números que já não descrevem a realidade;
- substituir e expirar deixam elo com a versão anterior, nunca apagam.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping, Optional

from src.domain.recommendations.entities import (
    TERMINAL_STATUSES,
    Recommendation,
    RecommendationStatus,
)
from src.domain.shared.enums import PlanStatus

#: Código do plano preventivo nascido de uma oportunidade, não de um risco.
#: Fica no mesmo espaço de nomes dos códigos do Radar de Fragilidade porque o
#: `PreventivePlan` é o mesmo — muda a origem, não a natureza do plano.
GOAL_ACCELERATION_PLAN_CODE = "GOAL_ACCELERATION_OPPORTUNITY"


class InvalidTransitionError(ValueError):
    pass


class StaleRecommendationError(ValueError):
    pass


def ensure_decidable(recommendation: Recommendation, current_fingerprint: str) -> None:
    """Barra a decisão quando a recomendação já foi decidida ou envelheceu."""
    if recommendation.status in TERMINAL_STATUSES:
        raise InvalidTransitionError(
            f"Recomendação já está em '{recommendation.status.value}' e não aceita nova decisão."
        )
    if recommendation.input_fingerprint != current_fingerprint:
        raise StaleRecommendationError(
            "Os dados financeiros mudaram desde esta análise. Recalcule antes de aprovar."
        )


def approve(
    recommendation: Recommendation,
    selected_scenario: str,
    plan_id: str,
    now: datetime,
) -> Recommendation:
    return replace(
        recommendation,
        status=RecommendationStatus.APPROVED,
        selected_scenario=selected_scenario,
        plan_id=plan_id,
        decided_at=now,
    )


def reject(recommendation: Recommendation, now: datetime) -> Recommendation:
    """Rejeitar não guarda cenário: não houve escolha, houve recusa."""
    return replace(
        recommendation,
        status=RecommendationStatus.REJECTED,
        selected_scenario=None,
        decided_at=now,
    )


def supersede(recommendation: Recommendation, successor_id: str) -> Recommendation:
    """Uma análise posterior encontrou outra coisa para o mesmo assunto."""
    if recommendation.status is not RecommendationStatus.PENDING:
        raise InvalidTransitionError("Só uma recomendação pendente pode ser substituída.")
    return replace(
        recommendation,
        status=RecommendationStatus.SUPERSEDED,
        superseded_by_id=successor_id,
    )


def expire(recommendation: Recommendation) -> Recommendation:
    """Os dados mudaram e a nova análise não encontrou nada no lugar."""
    if recommendation.status is not RecommendationStatus.PENDING:
        raise InvalidTransitionError("Só uma recomendação pendente pode expirar.")
    return replace(recommendation, status=RecommendationStatus.EXPIRED)


def _scenario_from(payload: Mapping[str, Any], key: str) -> Optional[Mapping[str, Any]]:
    for scenario in payload.get("scenarios", []):
        if scenario.get("key") == key:
            return scenario
    return None


def build_plan_payload(
    payload: Mapping[str, Any],
    selected_scenario: str,
    today: Optional[date] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Traduz o cenário aprovado nas `actions` de um plano preventivo.

    O plano é o que acompanha a execução, então ele guarda o compromisso
    (quanto por mês, até quando) — não o raciocínio inteiro, que já está
    preservado no registro da recomendação.
    """
    scenario = _scenario_from(payload, selected_scenario)
    if scenario is None:
        raise InvalidTransitionError(f"Cenário '{selected_scenario}' não existe nesta recomendação.")

    goal = payload.get("goal_description") or "sua meta principal"
    amount = scenario["additional_amount"]
    months = scenario.get("months_to_goal")
    completion = scenario.get("projected_completion")

    # `due_date` do plano = quando o compromisso termina. Sem prazo calculado,
    # cai no fim do mês corrente para não inventar uma data.
    reference = today or date.today()
    due_date = _period_to_date(completion) or reference.isoformat()

    actions = [
        {
            "description": (
                f"Direcionar {amount['amount']} {amount['currency']} adicionais por mês para "
                f"“{goal}”"
                + (f" durante {int(Decimal(str(months)))} meses." if months is not None else ".")
            ),
            "expected_monthly_impact": amount,
            "due_date": due_date,
        }
    ]

    expected_result = {
        "deficit_avoided": scenario.get("first_deficit_period") is None,
        "autonomy_change_months": _autonomy_delta(payload, scenario),
    }
    return actions, expected_result


def _period_to_date(period: Optional[str]) -> Optional[str]:
    """"2028-07" -> "2028-07-01"."""
    if not period or len(period) != 7:
        return None
    return f"{period}-01"


def _autonomy_delta(payload: Mapping[str, Any], scenario: Mapping[str, Any]) -> Optional[str]:
    before, after = payload.get("reserve_months"), scenario.get("autonomy_months_after")
    if before is None or after is None:
        return None
    return str(Decimal(str(after)) - Decimal(str(before)))


def initial_plan_status() -> PlanStatus:
    """O plano nasce aprovado: a decisão humana já aconteceu na recomendação.

    Aprovar aqui registra o compromisso — não movimenta dinheiro nenhum.
    """
    return PlanStatus.APPROVED
