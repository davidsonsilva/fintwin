# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel

from src.domain.decisions.entities import Simulation

_DECISION_TYPES = Literal[
    "CASH_PURCHASE",
    "INSTALLMENT_PURCHASE",
    "FINANCING",
    "LOAN",
    "INCOME_LOSS",
    "SALARY_REDUCTION",
    "NEW_RECURRING_EXPENSE",
    "NEW_GOAL",
    "RESERVE_INCREASE",
]


class ScenarioOverrideSchema(BaseModel):
    income_multiplier: Optional[str] = None
    essential_expense_multiplier: Optional[str] = None
    nonessential_expense_multiplier: Optional[str] = None
    unexpected_expense: Optional[str] = None
    expense_reduction_capacity: Optional[str] = None


class SimulationRequest(BaseModel):
    decision_type: _DECISION_TYPES
    parameters: dict[str, Any]
    scenario_override: Optional[ScenarioOverrideSchema] = None
    horizon_months: Literal[3, 6, 12] = 12


class SimulationResponse(BaseModel):
    id: str
    profile_id: str
    type: str
    parameters: dict[str, Any]
    baseline_result: dict[str, Any]
    simulated_result: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_domain(cls, simulation: Simulation) -> "SimulationResponse":
        return cls(
            id=simulation.id,
            profile_id=simulation.profile_id,
            type=simulation.type,
            parameters=dict(simulation.parameters),
            baseline_result=dict(simulation.baseline_result),
            simulated_result=dict(simulation.simulated_result),
            created_at=simulation.created_at,
        )
