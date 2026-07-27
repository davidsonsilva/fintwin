# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from src.domain.decisions.entities import FinancialGoal
from src.domain.shared.money import Money


class CreateGoalUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        profile_id: str,
        description: str,
        target_amount: Money,
        current_amount: Money,
        deadline: Optional[date],
        priority: int,
        monthly_contribution: Money,
    ) -> FinancialGoal:
        goal = FinancialGoal(
            id=str(uuid4()),
            profile_id=profile_id,
            description=description,
            target_amount=target_amount,
            current_amount=current_amount,
            deadline=deadline,
            priority=priority,
            monthly_contribution=monthly_contribution,
        )
        self._repo.add(goal)
        return goal
