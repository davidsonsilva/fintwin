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
