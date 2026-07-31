# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Cria um novo perfil e o popula com um dataset sintético rico (schema fintwin-demo/v2),
reutilizando os use cases de domínio (mesma validação do fluxo de onboarding real).

Uso (dentro do container da api):
    python scripts/seed_demo_v2.py /app/data/seed_v2.json
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.debt_use_cases import CreateDebtUseCase
from src.application.use_cases.event_use_cases import CreateEventUseCase
from src.application.use_cases.goal_use_cases import CreateGoalUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.domain.balance_history.entities import BalanceSnapshot
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.infrastructure.persistence.session import SessionLocal
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.balance_snapshot_repository import SqlAlchemyBalanceSnapshotRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository

ACCOUNT_TYPE_TO_LIQUIDITY = {
    "checking": LiquidityType.CHECKING_ACCOUNT,
    "investment": LiquidityType.INVESTMENT,
    "savings": LiquidityType.SAVINGS_ACCOUNT,
}

PRIORITY_TO_INT = {"low": 3, "medium": 2, "high": 1}

FISCAL_YEAR_START = date(2026, 1, 1)


def money(amount: float, currency: str) -> Money:
    return Money(Decimal(str(amount)), currency)


def main(json_path: str) -> None:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    session = SessionLocal()
    try:
        currency = data["profile"]["currency"]

        profile = CreateProfileUseCase(SqlAlchemyProfileRepository(session)).execute(
            currency=currency,
            dependents=len(data["profile"]["dependents"]),
            monthly_expense_reduction_capacity=Percentage(Decimal("0.15")),
            name=data["profile"].get("name"),
        )

        account_use_case = CreateAccountUseCase(SqlAlchemyAccountRepository(session))
        for item in data["accounts"]:
            account_use_case.execute(
                profile_id=profile.id,
                description=item["name"],
                balance=money(item["balance"], currency),
                liquidity_type=ACCOUNT_TYPE_TO_LIQUIDITY.get(item["type"], LiquidityType.OTHER),
                eligible_for_autonomy=not item.get("isPrimary", False),
            )

        income_use_case = CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session))
        for item in data["incomes"]:
            income_use_case.execute(
                profile_id=profile.id,
                description=f"{item['name']} - {item['source']}",
                amount=money(item["netAmount"], currency),
                frequency=Recurrence(item["frequency"]),
                start_date=FISCAL_YEAR_START,
                end_date=None,
                stability=IncomeStability.STABLE if item["type"] == "salary" else IncomeStability.VARIABLE,
            )

        obligation_use_case = CreateObligationUseCase(SqlAlchemyObligationRepository(session))
        for item in data["obligations"]:
            if not item.get("active", True):
                continue
            obligation_use_case.execute(
                profile_id=profile.id,
                description=item["name"],
                amount=money(item["amount"], currency),
                category=item["displayCategory"].lower(),
                frequency=Recurrence(item["frequency"]),
                due_day=item["dueDay"],
                start_date=FISCAL_YEAR_START,
                end_date=None,
                essential=item["essential"],
                debt_related=False,
            )

        debt_use_case = CreateDebtUseCase(SqlAlchemyDebtRepository(session))
        for item in data["debts"]:
            debt_use_case.execute(
                profile_id=profile.id,
                description=item["name"],
                outstanding_balance=money(item["outstandingBalance"], currency),
                installment_amount=money(item["installmentAmount"], currency),
                remaining_installments=item["remainingInstallments"],
                interest_rate_optional=f"{item['interestRateMonthlyPercent']}% a.m.",
                due_day=item["dueDay"],
            )

        goal_use_case = CreateGoalUseCase(SqlAlchemyGoalRepository(session))
        for item in data["goals"]:
            goal_use_case.execute(
                profile_id=profile.id,
                description=item["name"],
                target_amount=money(item["targetAmount"], currency),
                current_amount=money(item["currentAmount"], currency),
                deadline=date.fromisoformat(item["targetDate"]),
                priority=PRIORITY_TO_INT.get(item["priority"], 2),
                monthly_contribution=money(item["monthlyContribution"], currency),
            )

        event_use_case = CreateEventUseCase(SqlAlchemyEventRepository(session))
        for item in data["futureEvents"]:
            event_use_case.execute(
                profile_id=profile.id,
                description=item["name"],
                event_type=item["category"],
                amount=money(item["estimatedAmount"], currency),
                event_date=date.fromisoformat(item["date"]),
                recurrence=Recurrence.YEARLY if item.get("recurring") else None,
                direction=Direction.EXPENSE,
            )

        snapshot_repo = SqlAlchemyBalanceSnapshotRepository(session)
        for item in data["dashboard"]["monthlySnapshots"]:
            snapshot_repo.add(
                BalanceSnapshot(
                    id=str(uuid4()),
                    profile_id=profile.id,
                    period=item["month"],
                    net_balance=money(item["closingNetWorth"], currency),
                    created_at=datetime.utcnow(),
                )
            )

        print(f"profile_id={profile.id}")
    finally:
        session.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/app/data/seed_v2.json")
