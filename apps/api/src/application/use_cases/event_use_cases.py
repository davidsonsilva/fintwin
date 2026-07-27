# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from src.domain.cashflow.entities import FinancialEvent
from src.domain.shared.enums import Direction, Recurrence
from src.domain.shared.money import Money


class CreateEventUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(
        self,
        profile_id: str,
        description: str,
        event_type: str,
        amount: Money,
        event_date: date,
        recurrence: Optional[Recurrence],
        direction: Direction,
    ) -> FinancialEvent:
        event = FinancialEvent(
            id=str(uuid4()),
            profile_id=profile_id,
            description=description,
            event_type=event_type,
            amount=amount,
            date=event_date,
            recurrence=recurrence,
            direction=direction,
        )
        self._repo.add(event)
        return event
