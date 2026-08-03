# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Estrutura de saída do motor de oportunidade financeira proativa.

Diferente do Radar de Fragilidade (reativo a risco já instalado) e dos Planos
Preventivos (reação a um risco detectado), este motor responde à pergunta
oposta: *o orçamento está saudável — dá para usar essa folga sem criar um novo
risco?*

Nada aqui é texto pronto de recomendação. O motor devolve valores e códigos;
a formatação em pt-BR e a redação final são responsabilidade da borda.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Optional

from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage


class OpportunityStatus(str, Enum):
    """Os três desfechos possíveis da análise.

    O estado "analisando" não existe aqui: ele é o tempo de resposta da
    requisição, não um resultado do motor.
    """

    AVAILABLE = "available"
    NO_ACTION = "no_action"
    INSUFFICIENT_DATA = "insufficient_data"


class ScenarioKey(str, Enum):
    CONSERVATIVE = "conservative"
    RECOMMENDED = "recommended"
    ACCELERATED = "accelerated"
    #: Percentual escolhido pelo usuário em "Simular outro valor".
    CUSTOM = "custom"


class AnalysisDecision(str, Enum):
    """Decisão humana sobre a análise. Aprovar registra o plano — e só isso.

    O FinTwin não movimenta dinheiro em nenhuma dessas transições.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class OpportunityAnalysis:
    """Análise persistida — o que a tela `/recomendacoes/:analysisId` abre.

    `result` é o snapshot serializado do `OpportunityResult` no instante da
    geração. Ele nunca é recalculado: se os dados mudarem, a análise passa a
    ser reportada como defasada, mas os números que o usuário viu continuam
    intactos para auditoria.
    """

    id: str
    profile_id: str
    generated_at: datetime
    scenario: str
    status: OpportunityStatus
    input_fingerprint: str
    result: Mapping[str, Any]
    decision: AnalysisDecision
    decided_at: Optional[datetime]
    selected_scenario: Optional[str]


@dataclass
class EvidenceItem:
    """Um dado usado no diagnóstico, com a origem explícita.

    Só um dos campos de valor é preenchido; a borda renderiza o que vier
    diferente de `None`. Manter tipado (em vez de mandar string formatada)
    preserva a auditabilidade e deixa a formatação pt-BR no cliente.
    """

    key: str
    label: str
    money: Optional[Money] = None
    percentage: Optional[Percentage] = None
    months: Optional[Decimal] = None
    text: Optional[str] = None


@dataclass
class FundingSource:
    """De onde o dinheiro do aporte adicional sairia."""

    label: str
    amount: Money
    essential: bool


@dataclass
class OpportunityScenario:
    key: ScenarioKey
    additional_pct: Percentage
    additional_amount: Money
    new_monthly_contribution: Money
    months_to_goal: Optional[Decimal]
    months_saved: Optional[Decimal]
    projected_completion: Optional[str]  # "YYYY-MM"
    monthly_surplus_after: Money
    autonomy_months_after: Optional[Decimal]
    first_deficit_period: Optional[str]
    lowest_balance: Money
    safe: bool
    risks: list[str] = field(default_factory=list)


@dataclass
class OpportunityResult:
    status: OpportunityStatus
    currency: str
    generated_at: datetime

    # Por que não há recomendação (NO_ACTION) / o que falta (INSUFFICIENT_DATA).
    reason: Optional[str] = None
    missing_data: list[str] = field(default_factory=list)

    # Diagnóstico — preenchido sempre que houver renda para calcular.
    monthly_income: Optional[Money] = None
    monthly_obligations: Optional[Money] = None
    income_commitment: Optional[Percentage] = None
    essential_expenses_monthly: Optional[Money] = None
    recurring_surplus: Optional[Money] = None
    reserve_months: Optional[Decimal] = None

    # Meta principal (menor `priority`) e sua linha de base.
    goal_description: Optional[str] = None
    goal_target: Optional[Money] = None
    goal_current: Optional[Money] = None
    current_contribution: Optional[Money] = None
    current_contribution_pct: Optional[Percentage] = None
    baseline_months_to_goal: Optional[Decimal] = None
    baseline_completion: Optional[str] = None

    recommended: Optional[OpportunityScenario] = None
    scenarios: list[OpportunityScenario] = field(default_factory=list)
    funding_sources: list[FundingSource] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
