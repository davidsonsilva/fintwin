# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Snapshot mensal do saldo líquido, capturado de forma idempotente (Spec seção 15.1).

Não existe ledger de transações no domínio — este é o único registro de
histórico real, criado a partir de agora, nunca fabricado retroativamente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from src.domain.shared.money import Money

_PERIOD_PATTERN = re.compile(r"^\d{4}-\d{2}$")


@dataclass
class BalanceSnapshot:
    id: str
    profile_id: str
    period: str
    net_balance: Money
    created_at: datetime

    def __post_init__(self) -> None:
        if not _PERIOD_PATTERN.match(self.period):
            raise ValueError("period deve estar no formato 'YYYY-MM'.")
