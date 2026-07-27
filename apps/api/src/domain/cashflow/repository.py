# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Interface de repositório para FinancialEvent (agregado cashflow)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.cashflow.entities import FinancialEvent


class EventRepository(Protocol):
    def add(self, event: FinancialEvent) -> None: ...
    def get(self, event_id: str) -> Optional[FinancialEvent]: ...
    def list_by_profile(self, profile_id: str) -> list[FinancialEvent]: ...
    def update(self, event: FinancialEvent) -> None: ...
    def delete(self, event_id: str) -> None: ...
