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
from src.domain.recommendations.entities import InsightSurface, Recommendation
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


class RecommendationResponse(BaseModel):
    """Uma entrada do Registro de Recomendações."""

    id: str
    profile_id: str
    kind: str
    source: str
    status: str
    generated_at: datetime
    scenario: str
    #: Depende do agora, então nunca entra no snapshot persistido.
    stale: bool = False
    decided_at: Optional[datetime] = None
    selected_scenario: Optional[str] = None
    supersedes_id: Optional[str] = None
    superseded_by_id: Optional[str] = None
    plan_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    payload: dict[str, Any]

    @classmethod
    def from_domain(cls, recommendation: Recommendation, stale: bool = False) -> "RecommendationResponse":
        return cls(
            id=recommendation.id,
            profile_id=recommendation.profile_id,
            kind=recommendation.kind.value,
            source=recommendation.source.value,
            status=recommendation.status.value,
            generated_at=recommendation.generated_at,
            scenario=recommendation.scenario,
            stale=stale,
            decided_at=recommendation.decided_at,
            selected_scenario=recommendation.selected_scenario,
            supersedes_id=recommendation.supersedes_id,
            superseded_by_id=recommendation.superseded_by_id,
            plan_id=recommendation.plan_id,
            conversation_id=recommendation.conversation_id,
            message_id=recommendation.message_id,
            payload=dict(recommendation.payload),
        )


class InsightResponse(BaseModel):
    """O que o card Insight consome.

    Ou vem uma recomendação pendente, ou vem o diagnóstico corrente explicando
    por que não há ação. Nunca as duas coisas.
    """

    recommendation: Optional[RecommendationResponse] = None
    diagnosis: Optional[OpportunityResultResponse] = None
    #: Plano em execução para o assunto — o card cita e segue monitorando.
    active_plan_id: Optional[str] = None

    @classmethod
    def from_domain(cls, surface: InsightSurface) -> "InsightResponse":
        return cls(
            recommendation=(
                RecommendationResponse.from_domain(surface.recommendation, surface.stale)
                if surface.recommendation is not None
                else None
            ),
            diagnosis=(
                OpportunityResultResponse.model_validate(surface.diagnosis)
                if surface.diagnosis is not None
                else None
            ),
            active_plan_id=surface.active_plan_id,
        )


class DetectRequest(BaseModel):
    #: "Simular outro valor": fração da renda (0.03 = 3%).
    custom_pct: Optional[Decimal] = Field(default=None, ge=0, le=1)


class DecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    selected_scenario: Optional[str] = None


class ConversationRecommendationRequest(BaseModel):
    """Salvar como recomendação, a partir de uma resposta do agente.

    Exige o vínculo com a mensagem: sem ele não dá para auditar de onde a
    recomendação saiu.
    """

    conversation_id: str
    message_id: str
    payload: dict[str, Any]
