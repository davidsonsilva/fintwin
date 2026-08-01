# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Mapping, Optional

from pydantic import BaseModel, Field

from src.domain.opportunity.entities import OpportunityResult
from src.interfaces.http.schemas.common import MoneySchema


class EvidenceItemResponse(BaseModel):
    key: str
    label: str
    money: Optional[MoneySchema] = None
    percentage: Optional[Decimal] = None
    months: Optional[Decimal] = None
    text: Optional[str] = None


class FundingSourceResponse(BaseModel):
    label: str
    amount: MoneySchema
    essential: bool


class OpportunityScenarioResponse(BaseModel):
    key: str
    additional_pct: Decimal
    additional_amount: MoneySchema
    new_monthly_contribution: MoneySchema
    months_to_goal: Optional[Decimal]
    months_saved: Optional[Decimal]
    projected_completion: Optional[str]
    monthly_surplus_after: MoneySchema
    autonomy_months_after: Optional[Decimal]
    first_deficit_period: Optional[str]
    lowest_balance: MoneySchema
    safe: bool
    risks: list[str]


class OpportunityResultResponse(BaseModel):
    """O snapshot do motor. É exatamente isto que é persistido em JSON."""

    status: str
    currency: str
    generated_at: datetime
    reason: Optional[str] = None
    missing_data: list[str] = Field(default_factory=list)

    monthly_income: Optional[MoneySchema] = None
    monthly_obligations: Optional[MoneySchema] = None
    income_commitment: Optional[Decimal] = None
    essential_expenses_monthly: Optional[MoneySchema] = None
    recurring_surplus: Optional[MoneySchema] = None
    reserve_months: Optional[Decimal] = None

    goal_description: Optional[str] = None
    goal_target: Optional[MoneySchema] = None
    goal_current: Optional[MoneySchema] = None
    current_contribution: Optional[MoneySchema] = None
    current_contribution_pct: Optional[Decimal] = None
    baseline_months_to_goal: Optional[Decimal] = None
    baseline_completion: Optional[str] = None

    recommended: Optional[OpportunityScenarioResponse] = None
    scenarios: list[OpportunityScenarioResponse] = Field(default_factory=list)
    funding_sources: list[FundingSourceResponse] = Field(default_factory=list)
    evidence: list[EvidenceItemResponse] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: OpportunityResult) -> "OpportunityResultResponse":
        def money(value) -> Optional[MoneySchema]:
            return MoneySchema.from_domain(value) if value is not None else None

        def pct(value) -> Optional[Decimal]:
            return value.as_fraction() if value is not None else None

        def scenario(item) -> OpportunityScenarioResponse:
            return OpportunityScenarioResponse(
                key=item.key.value,
                additional_pct=item.additional_pct.as_fraction(),
                additional_amount=MoneySchema.from_domain(item.additional_amount),
                new_monthly_contribution=MoneySchema.from_domain(item.new_monthly_contribution),
                months_to_goal=item.months_to_goal,
                months_saved=item.months_saved,
                projected_completion=item.projected_completion,
                monthly_surplus_after=MoneySchema.from_domain(item.monthly_surplus_after),
                autonomy_months_after=item.autonomy_months_after,
                first_deficit_period=item.first_deficit_period,
                lowest_balance=MoneySchema.from_domain(item.lowest_balance),
                safe=item.safe,
                risks=item.risks,
            )

        return cls(
            status=result.status.value,
            currency=result.currency,
            generated_at=result.generated_at,
            reason=result.reason,
            missing_data=result.missing_data,
            monthly_income=money(result.monthly_income),
            monthly_obligations=money(result.monthly_obligations),
            income_commitment=pct(result.income_commitment),
            essential_expenses_monthly=money(result.essential_expenses_monthly),
            recurring_surplus=money(result.recurring_surplus),
            reserve_months=result.reserve_months,
            goal_description=result.goal_description,
            goal_target=money(result.goal_target),
            goal_current=money(result.goal_current),
            current_contribution=money(result.current_contribution),
            current_contribution_pct=pct(result.current_contribution_pct),
            baseline_months_to_goal=result.baseline_months_to_goal,
            baseline_completion=result.baseline_completion,
            recommended=scenario(result.recommended) if result.recommended else None,
            scenarios=[scenario(item) for item in result.scenarios],
            funding_sources=[
                FundingSourceResponse(
                    label=source.label,
                    amount=MoneySchema.from_domain(source.amount),
                    essential=source.essential,
                )
                for source in result.funding_sources
            ],
            evidence=[
                EvidenceItemResponse(
                    key=item.key,
                    label=item.label,
                    money=money(item.money),
                    percentage=pct(item.percentage),
                    months=item.months,
                    text=item.text,
                )
                for item in result.evidence
            ],
            risks=result.risks,
            assumptions=result.assumptions,
        )

    def to_payload(self) -> Mapping[str, Any]:
        """Forma persistida: JSON puro, sem Decimal nem datetime."""
        return self.model_dump(mode="json")


class OpportunityAnalysisResponse(BaseModel):
    """Envelope versionado que a tela `/recomendacoes/:analysisId` consome."""

    analysis_id: str
    profile_id: str
    generated_at: datetime
    scenario: str
    #: `stale` só existe aqui, nunca no snapshot: ele depende do agora.
    stale: bool
    decision: str
    decided_at: Optional[datetime] = None
    selected_scenario: Optional[str] = None
    result: OpportunityResultResponse

    @classmethod
    def from_domain(cls, loaded) -> "OpportunityAnalysisResponse":
        analysis = loaded.analysis
        return cls(
            analysis_id=analysis.id,
            profile_id=analysis.profile_id,
            generated_at=analysis.generated_at,
            scenario=analysis.scenario,
            stale=loaded.stale,
            decision=analysis.decision.value,
            decided_at=analysis.decided_at,
            selected_scenario=analysis.selected_scenario,
            result=OpportunityResultResponse.model_validate(analysis.result),
        )


class OpportunityAnalysisRequest(BaseModel):
    #: "Simular outro valor": fração da renda (0.03 = 3%). Opcional.
    custom_pct: Optional[Decimal] = Field(default=None, ge=0, le=1)


class OpportunityDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    selected_scenario: Optional[str] = None
