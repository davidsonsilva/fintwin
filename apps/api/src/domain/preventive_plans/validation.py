# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Transições de status permitidas para um PreventivePlan (Spec seção 6.7)."""

from __future__ import annotations

from src.domain.shared.enums import PlanStatus

PLAN_STATUS_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.PROPOSED: {PlanStatus.APPROVED, PlanStatus.REJECTED},
    PlanStatus.APPROVED: {PlanStatus.IN_PROGRESS, PlanStatus.CANCELLED},
    PlanStatus.IN_PROGRESS: {PlanStatus.COMPLETED, PlanStatus.CANCELLED},
    PlanStatus.REJECTED: set(),
    PlanStatus.COMPLETED: set(),
    PlanStatus.CANCELLED: set(),
}


class InvalidPlanStatusTransitionError(ValueError):
    pass


def validate_status_transition(current: PlanStatus, new: PlanStatus) -> None:
    allowed = PLAN_STATUS_TRANSITIONS[current]
    if new not in allowed:
        raise InvalidPlanStatusTransitionError(
            f"Transição inválida: {current.value} -> {new.value}."
        )
