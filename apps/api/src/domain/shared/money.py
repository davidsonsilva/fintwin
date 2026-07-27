# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Value Object Money (Spec seção 15.2).

Requisitos obrigatórios:
- usar Decimal;
- proibir float;
- armazenar moeda;
- impedir operações entre moedas diferentes;
- aplicar arredondamento definido;
- rejeitar valor inválido;
- serializar como string em JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_QUANTIZATION = Decimal("0.01")


class InvalidMoneyError(ValueError):
    pass


class CurrencyMismatchError(ValueError):
    pass


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, float):
            raise InvalidMoneyError("Money não aceita float; use Decimal ou str.")
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except InvalidOperation as exc:
                raise InvalidMoneyError(f"Valor monetário inválido: {self.amount!r}") from exc
        if not self.currency or not isinstance(self.currency, str):
            raise InvalidMoneyError("Money requer uma moeda válida.")
        quantized = self.amount.quantize(_QUANTIZATION, rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)
        object.__setattr__(self, "currency", self.currency.upper())

    def _ensure_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Não é possível operar entre moedas diferentes: {self.currency} e {other.currency}."
            )

    def add(self, other: "Money") -> "Money":
        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._ensure_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: Decimal) -> "Money":
        if isinstance(factor, float):
            raise InvalidMoneyError("Multiplicador não pode ser float; use Decimal.")
        return Money(self.amount * Decimal(factor), self.currency)

    def is_negative(self) -> bool:
        return self.amount < Decimal("0")

    def to_json(self) -> str:
        return str(self.amount)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
