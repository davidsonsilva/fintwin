from __future__ import annotations

from pydantic import BaseModel, Field

from src.domain.financial_profile.entities import FinancialAccount
from src.domain.shared.enums import LiquidityType
from src.interfaces.http.schemas.common import MoneySchema


class AccountCreateRequest(BaseModel):
    description: str = Field(min_length=1)
    balance: MoneySchema
    liquidity_type: LiquidityType
    eligible_for_autonomy: bool = False


class AccountResponse(BaseModel):
    id: str
    profile_id: str
    description: str
    balance: MoneySchema
    liquidity_type: LiquidityType
    eligible_for_autonomy: bool

    @classmethod
    def from_domain(cls, account: FinancialAccount) -> "AccountResponse":
        return cls(
            id=account.id,
            profile_id=account.profile_id,
            description=account.description,
            balance=MoneySchema.from_domain(account.balance),
            liquidity_type=account.liquidity_type,
            eligible_for_autonomy=account.eligible_for_autonomy,
        )
