from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from src.domain.decisions.entities import FinancialGoal
from src.interfaces.http.schemas.common import MoneySchema


class GoalCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    target_amount: MoneySchema
    current_amount: MoneySchema
    deadline: Optional[date] = None
    priority: int = Field(ge=1)
    monthly_contribution: MoneySchema


class GoalResponse(BaseModel):
    id: str
    profile_id: str
    description: str
    target_amount: MoneySchema
    current_amount: MoneySchema
    deadline: Optional[date]
    priority: int
    monthly_contribution: MoneySchema

    @classmethod
    def from_domain(cls, goal: FinancialGoal) -> "GoalResponse":
        return cls(
            id=goal.id,
            profile_id=goal.profile_id,
            description=goal.description,
            target_amount=MoneySchema.from_domain(goal.target_amount),
            current_amount=MoneySchema.from_domain(goal.current_amount),
            deadline=goal.deadline,
            priority=goal.priority,
            monthly_contribution=MoneySchema.from_domain(goal.monthly_contribution),
        )
