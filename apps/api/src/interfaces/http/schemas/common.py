# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Schemas Pydantic compartilhados na borda HTTP (conversão Money <-> JSON)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from src.domain.shared.money import Money


class MoneySchema(BaseModel):
    amount: Decimal
    currency: str

    def to_domain(self) -> Money:
        return Money(self.amount, self.currency)

    @classmethod
    def from_domain(cls, money: Money) -> "MoneySchema":
        return cls(amount=money.amount, currency=money.currency)
