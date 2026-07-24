"""Value Object Percentage (Spec seção 15.2)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_MIN = Decimal("0")
_MAX = Decimal("1")


class InvalidPercentageError(ValueError):
    pass


@dataclass(frozen=True)
class Percentage:
    """Representa uma fração entre 0 e 1 (ex: 0.80 = 80%)."""

    value: Decimal

    def __post_init__(self) -> None:
        if isinstance(self.value, float):
            raise InvalidPercentageError("Percentage não aceita float; use Decimal ou str.")
        if not isinstance(self.value, Decimal):
            try:
                object.__setattr__(self, "value", Decimal(str(self.value)))
            except InvalidOperation as exc:
                raise InvalidPercentageError(f"Percentual inválido: {self.value!r}") from exc
        if self.value < _MIN or self.value > _MAX:
            raise InvalidPercentageError(
                f"Percentage deve estar entre 0 e 1, recebido {self.value}."
            )

    def as_fraction(self) -> Decimal:
        return self.value

    def as_display_percent(self) -> Decimal:
        return self.value * Decimal("100")

    def to_json(self) -> str:
        return str(self.value)

    def __str__(self) -> str:
        return f"{self.as_display_percent()}%"
