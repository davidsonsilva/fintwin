# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Estrutura de saída do Índice de Autonomia Financeira (Spec seção 9)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import FinancialObligation
from src.domain.shared.money import Money


@dataclass
class AutonomyResult:
    eligible_assets: Money
    essential_expenses_monthly: Money
    basic_autonomy_months: Optional[Decimal]

    probable_monthly_burn: Money
    adverse_monthly_burn: Money
    income_loss_monthly_burn: Money
    probable_autonomy_months: Optional[Decimal]
    adverse_autonomy_months: Optional[Decimal]
    income_loss_autonomy_months: Optional[Decimal]

    eligible_accounts: list[FinancialAccount]
    essential_obligations: list[FinancialObligation]
    assumptions: list[str]
