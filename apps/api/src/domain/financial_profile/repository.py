# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Interfaces de repositório do agregado FinancialProfile (Spec seção 23: repositórios por interface)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.financial_profile.entities import FinancialAccount, FinancialProfile


class ProfileRepository(Protocol):
    def add(self, profile: FinancialProfile) -> None: ...

    def get(self, profile_id: str) -> Optional[FinancialProfile]: ...

    def update(self, profile: FinancialProfile) -> None: ...


class AccountRepository(Protocol):
    def add(self, account: FinancialAccount) -> None: ...

    def get(self, account_id: str) -> Optional[FinancialAccount]: ...

    def list_by_profile(self, profile_id: str) -> list[FinancialAccount]: ...

    def update(self, account: FinancialAccount) -> None: ...

    def delete(self, account_id: str) -> None: ...
