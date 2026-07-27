# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel

from src.domain.preventive_plans.entities import PreventivePlan

_PLAN_STATUS_VALUES = Literal["proposed", "approved", "rejected", "in_progress", "completed", "cancelled"]


class PreventivePlanResponse(BaseModel):
    id: str
    profile_id: str
    risk_code: str
    status: str
    actions: list[dict[str, Any]]
    expected_result: dict[str, Any]
    created_at: datetime
    approved_at: Optional[datetime]

    @classmethod
    def from_domain(cls, plan: PreventivePlan) -> "PreventivePlanResponse":
        return cls(
            id=plan.id,
            profile_id=plan.profile_id,
            risk_code=plan.risk_code,
            status=plan.status.value,
            actions=list(plan.actions),
            expected_result=dict(plan.expected_result),
            created_at=plan.created_at,
            approved_at=plan.approved_at,
        )


class PlanStatusUpdateRequest(BaseModel):
    status: _PLAN_STATUS_VALUES
