# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Interface de repositório para BalanceSnapshot."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.balance_history.entities import BalanceSnapshot


class BalanceSnapshotRepository(Protocol):
    def add(self, snapshot: BalanceSnapshot) -> None: ...
    def get_by_profile_and_period(self, profile_id: str, period: str) -> Optional[BalanceSnapshot]: ...
    def list_by_profile_ordered(self, profile_id: str, limit: int) -> list[BalanceSnapshot]: ...
