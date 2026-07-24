"""Interface de repositório para PreventivePlan (Spec seção 15.1)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.preventive_plans.entities import PreventivePlan


class PreventivePlanRepository(Protocol):
    def add(self, plan: PreventivePlan) -> None: ...
    def get(self, plan_id: str) -> Optional[PreventivePlan]: ...
    def list_by_profile(self, profile_id: str) -> list[PreventivePlan]: ...
    def update(self, plan: PreventivePlan) -> None: ...
