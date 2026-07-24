from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel

from src.domain.projection.entities import PeriodProjection, ProjectionResult
from src.interfaces.http.schemas.common import MoneySchema
from src.interfaces.http.schemas.event import EventResponse


class ProjectionRequest(BaseModel):
    months: Literal[3, 6, 12] = 12
    scenario: Literal["probable", "adverse"] = "probable"
    parameters: Optional[dict[str, Any]] = None


class PeriodProjectionResponse(BaseModel):
    period: str
    opening_balance: MoneySchema
    income_total: MoneySchema
    expense_total: MoneySchema
    net_cashflow: MoneySchema
    closing_balance: MoneySchema
    income_commitment_percentage: Optional[Decimal]
    deficit: bool

    @classmethod
    def from_domain(cls, period: PeriodProjection) -> "PeriodProjectionResponse":
        return cls(
            period=period.period,
            opening_balance=MoneySchema.from_domain(period.opening_balance),
            income_total=MoneySchema.from_domain(period.income_total),
            expense_total=MoneySchema.from_domain(period.expense_total),
            net_cashflow=MoneySchema.from_domain(period.net_cashflow),
            closing_balance=MoneySchema.from_domain(period.closing_balance),
            income_commitment_percentage=(
                period.income_commitment_percentage.as_fraction()
                if period.income_commitment_percentage is not None
                else None
            ),
            deficit=period.deficit,
        )


class ProjectionResponse(BaseModel):
    scenario: str
    periods: list[PeriodProjectionResponse]
    first_deficit_period: Optional[str]
    lowest_balance: MoneySchema
    final_balance: MoneySchema
    total_income: MoneySchema
    total_expenses: MoneySchema
    main_pressures: list[str]
    relevant_events: list[EventResponse]
    assumptions: list[str]

    @classmethod
    def from_domain(cls, result: ProjectionResult) -> "ProjectionResponse":
        return cls(
            scenario=result.scenario.value,
            periods=[PeriodProjectionResponse.from_domain(period) for period in result.periods],
            first_deficit_period=result.first_deficit_period,
            lowest_balance=MoneySchema.from_domain(result.lowest_balance),
            final_balance=MoneySchema.from_domain(result.final_balance),
            total_income=MoneySchema.from_domain(result.total_income),
            total_expenses=MoneySchema.from_domain(result.total_expenses),
            main_pressures=result.main_pressures,
            relevant_events=[EventResponse.from_domain(event) for event in result.relevant_events],
            assumptions=result.assumptions,
        )
