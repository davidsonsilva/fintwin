# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.opportunity.entities import AnalysisDecision, OpportunityAnalysis, OpportunityStatus
from src.infrastructure.persistence.models import OpportunityAnalysisModel


def _to_entity(model: OpportunityAnalysisModel) -> OpportunityAnalysis:
    return OpportunityAnalysis(
        id=model.id,
        profile_id=model.profile_id,
        generated_at=model.generated_at,
        scenario=model.scenario,
        status=OpportunityStatus(model.status),
        input_fingerprint=model.input_fingerprint,
        result=dict(model.result),
        decision=AnalysisDecision(model.decision),
        decided_at=model.decided_at,
        selected_scenario=model.selected_scenario,
    )


class SqlAlchemyOpportunityAnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, analysis: OpportunityAnalysis) -> OpportunityAnalysis:
        model = OpportunityAnalysisModel(
            id=analysis.id,
            profile_id=analysis.profile_id,
            generated_at=analysis.generated_at,
            scenario=analysis.scenario,
            status=analysis.status.value,
            input_fingerprint=analysis.input_fingerprint,
            result=dict(analysis.result),
            decision=analysis.decision.value,
            decided_at=analysis.decided_at,
            selected_scenario=analysis.selected_scenario,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get(self, analysis_id: str) -> Optional[OpportunityAnalysis]:
        model = self._session.get(OpportunityAnalysisModel, analysis_id)
        return _to_entity(model) if model is not None else None

    def get_latest_for_profile(self, profile_id: str) -> Optional[OpportunityAnalysis]:
        stmt = (
            select(OpportunityAnalysisModel)
            .where(OpportunityAnalysisModel.profile_id == profile_id)
            .order_by(OpportunityAnalysisModel.generated_at.desc())
            .limit(1)
        )
        model = self._session.execute(stmt).scalars().first()
        return _to_entity(model) if model is not None else None

    def record_decision(
        self,
        analysis_id: str,
        decision: AnalysisDecision,
        selected_scenario: Optional[str],
        decided_at,
    ) -> Optional[OpportunityAnalysis]:
        model = self._session.get(OpportunityAnalysisModel, analysis_id)
        if model is None:
            return None
        model.decision = decision.value
        model.selected_scenario = selected_scenario
        model.decided_at = decided_at
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)
