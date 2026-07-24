from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from src.application.use_cases.dashboard_use_cases import DashboardSummary
from src.domain.cashflow.entities import FinancialEvent
from src.interfaces.http.schemas.common import MoneySchema


class MainGoalSummaryResponse(BaseModel):
    description: str
    progress_pct: Decimal


class UpcomingEventResponse(BaseModel):
    id: str
    description: str
    event_type: str
    amount: MoneySchema
    date: date
    direction: str

    @classmethod
    def from_domain(cls, event: FinancialEvent) -> "UpcomingEventResponse":
        return cls(
            id=event.id,
            description=event.description,
            event_type=event.event_type,
            amount=MoneySchema.from_domain(event.amount),
            date=event.date,
            direction=event.direction.value,
        )


class DashboardSummaryResponse(BaseModel):
    net_balance: MoneySchema
    monthly_obligations_total: MoneySchema
    income_commitment_pct: Optional[Decimal]
    main_goal: Optional[MainGoalSummaryResponse]
    upcoming_events: list[UpcomingEventResponse]

    @classmethod
    def from_domain(cls, summary: DashboardSummary) -> "DashboardSummaryResponse":
        return cls(
            net_balance=MoneySchema.from_domain(summary.net_balance),
            monthly_obligations_total=MoneySchema.from_domain(summary.monthly_obligations_total),
            income_commitment_pct=(
                summary.income_commitment_pct.as_fraction() if summary.income_commitment_pct is not None else None
            ),
            main_goal=(
                MainGoalSummaryResponse(
                    description=summary.main_goal.description,
                    progress_pct=summary.main_goal.progress_pct.as_fraction(),
                )
                if summary.main_goal is not None
                else None
            ),
            upcoming_events=[UpcomingEventResponse.from_domain(event) for event in summary.upcoming_events],
        )
