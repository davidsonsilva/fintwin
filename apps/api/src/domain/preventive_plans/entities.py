"""Entidade PreventivePlan (Spec seções 13 e 15.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from src.domain.shared.enums import PlanStatus


@dataclass
class PreventivePlan:
    id: str
    profile_id: str
    risk_code: str
    status: PlanStatus
    actions: Sequence[Mapping[str, Any]]
    expected_result: Mapping[str, Any]
    created_at: datetime
    approved_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.risk_code:
            raise ValueError("PreventivePlan requer risk_code.")
        if not self.actions:
            raise ValueError("PreventivePlan requer ao menos uma action.")
