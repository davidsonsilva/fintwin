# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Casos de uso da recomendação financeira proativa.

Gerar é uma escrita: cada clique em "Ver recomendações" cria uma análise nova,
com id próprio, e é ela que a tela abre. Abrir é uma leitura pura — nada é
recalculado, só se confere se os dados mudaram desde então.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Mapping, Optional
from uuid import uuid4

from src.domain.opportunity.engine import analyze_opportunity
from src.domain.opportunity.entities import (
    AnalysisDecision,
    OpportunityAnalysis,
    OpportunityResult,
)
from src.domain.opportunity.fingerprint import compute_input_fingerprint

#: Único cenário de projeção usado hoje. Fica explícito no registro para que
#: uma análise antiga continue legível se outros cenários entrarem depois.
ANALYSIS_SCENARIO = "probable"

Serializer = Callable[[OpportunityResult], Mapping[str, Any]]


@dataclass
class LoadedAnalysis:
    """Uma análise persistida somada ao veredito de frescor."""

    analysis: OpportunityAnalysis
    stale: bool


class _ProfileDataLoader:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo

    def load(self, profile_id: str) -> dict[str, Any]:
        return {
            "accounts": self._account_repo.list_by_profile(profile_id),
            "incomes": self._income_repo.list_by_profile(profile_id),
            "obligations": self._obligation_repo.list_by_profile(profile_id),
            "debts": self._debt_repo.list_by_profile(profile_id),
            "goals": self._goal_repo.list_by_profile(profile_id),
            "events": self._event_repo.list_by_profile(profile_id),
        }


class CreateOpportunityAnalysisUseCase:
    """Roda o motor e congela o resultado num registro auditável."""

    def __init__(
        self,
        analysis_repo: Any,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
        serializer: Serializer,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._loader = _ProfileDataLoader(
            account_repo, income_repo, obligation_repo, debt_repo, goal_repo, event_repo
        )
        self._serialize = serializer

    def execute(
        self, profile_id: str, currency: str, custom_pct: Optional[Decimal] = None
    ) -> LoadedAnalysis:
        data = self._loader.load(profile_id)
        result = analyze_opportunity(currency=currency, custom_pct=custom_pct, **data)
        fingerprint = compute_input_fingerprint(currency=currency, **data)

        analysis = self._analysis_repo.add(
            OpportunityAnalysis(
                id=str(uuid4()),
                profile_id=profile_id,
                generated_at=result.generated_at,
                scenario=ANALYSIS_SCENARIO,
                status=result.status,
                input_fingerprint=fingerprint,
                result=self._serialize(result),
                decision=AnalysisDecision.PENDING,
                decided_at=None,
                selected_scenario=None,
            )
        )
        return LoadedAnalysis(analysis=analysis, stale=False)


class GetOpportunityAnalysisUseCase:
    """Lê a análise guardada e diz se ela envelheceu.

    Não recalcula nada: recalcular em silêncio trocaria os números sob os pés
    de quem está decidindo.
    """

    def __init__(
        self,
        analysis_repo: Any,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._loader = _ProfileDataLoader(
            account_repo, income_repo, obligation_repo, debt_repo, goal_repo, event_repo
        )

    def execute(self, analysis_id: str, currency: str) -> Optional[LoadedAnalysis]:
        analysis = self._analysis_repo.get(analysis_id)
        if analysis is None:
            return None
        current = compute_input_fingerprint(
            currency=currency, **self._loader.load(analysis.profile_id)
        )
        return LoadedAnalysis(analysis=analysis, stale=current != analysis.input_fingerprint)


class DecideOpportunityAnalysisUseCase:
    """Registra a decisão humana. Nenhum dinheiro se move aqui."""

    def __init__(self, analysis_repo: Any) -> None:
        self._analysis_repo = analysis_repo

    def execute(
        self,
        analysis_id: str,
        decision: AnalysisDecision,
        selected_scenario: Optional[str],
    ) -> Optional[OpportunityAnalysis]:
        return self._analysis_repo.record_decision(
            analysis_id=analysis_id,
            decision=decision,
            selected_scenario=selected_scenario if decision == AnalysisDecision.APPROVED else None,
            decided_at=datetime.utcnow(),
        )
