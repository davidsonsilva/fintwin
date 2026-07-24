from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from src.domain.autonomy.entities import AutonomyResult
from src.interfaces.http.schemas.account import AccountResponse
from src.interfaces.http.schemas.common import MoneySchema
from src.interfaces.http.schemas.obligation import ObligationResponse


class AutonomyResponse(BaseModel):
    eligible_assets: MoneySchema
    essential_expenses_monthly: MoneySchema
    basic_autonomy_months: Optional[Decimal]

    probable_monthly_burn: MoneySchema
    adverse_monthly_burn: MoneySchema
    income_loss_monthly_burn: MoneySchema
    probable_autonomy_months: Optional[Decimal]
    adverse_autonomy_months: Optional[Decimal]
    income_loss_autonomy_months: Optional[Decimal]

    eligible_accounts: list[AccountResponse]
    essential_obligations: list[ObligationResponse]
    assumptions: list[str]

    @classmethod
    def from_domain(cls, result: AutonomyResult) -> "AutonomyResponse":
        return cls(
            eligible_assets=MoneySchema.from_domain(result.eligible_assets),
            essential_expenses_monthly=MoneySchema.from_domain(result.essential_expenses_monthly),
            basic_autonomy_months=result.basic_autonomy_months,
            probable_monthly_burn=MoneySchema.from_domain(result.probable_monthly_burn),
            adverse_monthly_burn=MoneySchema.from_domain(result.adverse_monthly_burn),
            income_loss_monthly_burn=MoneySchema.from_domain(result.income_loss_monthly_burn),
            probable_autonomy_months=result.probable_autonomy_months,
            adverse_autonomy_months=result.adverse_autonomy_months,
            income_loss_autonomy_months=result.income_loss_autonomy_months,
            eligible_accounts=[AccountResponse.from_domain(account) for account in result.eligible_accounts],
            essential_obligations=[
                ObligationResponse.from_domain(obligation) for obligation in result.essential_obligations
            ],
            assumptions=result.assumptions,
        )
