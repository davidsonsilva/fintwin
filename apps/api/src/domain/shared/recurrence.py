# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Normalização de valores recorrentes para equivalente mensal (Spec seção 8/9).

Reaproveitado pelo resumo do dashboard (VS-03) e pelo motor de projeção (VS-04).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.domain.shared.enums import Recurrence
from src.domain.shared.money import Money

_WEEKS_PER_MONTH = Decimal("52") / Decimal("12")
_MONTHS_PER_YEAR = Decimal("12")


def monthly_equivalent(amount: Money, frequency: Recurrence) -> Optional[Money]:
    """Normaliza um valor recorrente para seu equivalente mensal.

    `one_off` não é recorrente, então é excluído dos totais mensalizados
    (quem precisa do valor pontual deve tratá-lo separadamente pela data).
    """
    if frequency == Recurrence.MONTHLY:
        return amount
    if frequency == Recurrence.WEEKLY:
        return amount.multiply(_WEEKS_PER_MONTH)
    if frequency == Recurrence.YEARLY:
        return amount.multiply(Decimal("1") / _MONTHS_PER_YEAR)
    return None
