# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Carrega o perfil fictício de demonstração (data/demo/*.json) para um profile_id existente."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.domain.balance_history.entities import BalanceSnapshot
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money

def _default_demo_dir() -> Path:
    # Em dev local o repo inteiro está presente; em Docker o build context é
    # só apps/api, então data/ não existe e DEMO_DATA_DIR deve ser setado.
    file_parents = Path(__file__).resolve().parents
    if len(file_parents) > 5:
        return file_parents[5] / "data" / "demo"
    return Path("/app/data/demo")


DEMO_DIR = Path(os.environ.get("DEMO_DATA_DIR", str(_default_demo_dir())))


def _money(data: dict[str, Any]) -> Money:
    return Money(Decimal(data["amount"]), data["currency"])


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _load(filename: str) -> Any:
    return json.loads((DEMO_DIR / filename).read_text(encoding="utf-8"))


class LoadDemoProfileUseCase:
    """Popula um perfil já existente com os dados fictícios de demonstração."""

    def __init__(
        self,
        account_use_case: Any,
        income_use_case: Any,
        obligation_use_case: Any,
        debt_use_case: Any,
        goal_use_case: Any,
        event_use_case: Any,
        balance_snapshot_repo: Any = None,
    ) -> None:
        self._account_use_case = account_use_case
        self._income_use_case = income_use_case
        self._obligation_use_case = obligation_use_case
        self._debt_use_case = debt_use_case
        self._goal_use_case = goal_use_case
        self._event_use_case = event_use_case
        self._balance_snapshot_repo = balance_snapshot_repo

    def execute(self, profile_id: str) -> None:
        for item in _load("accounts.json"):
            self._account_use_case.execute(
                profile_id=profile_id,
                description=item["description"],
                balance=_money(item["balance"]),
                liquidity_type=LiquidityType(item["liquidity_type"]),
                eligible_for_autonomy=item["eligible_for_autonomy"],
            )

        for item in _load("incomes.json"):
            self._income_use_case.execute(
                profile_id=profile_id,
                description=item["description"],
                amount=_money(item["amount"]),
                frequency=Recurrence(item["frequency"]),
                start_date=_date(item["start_date"]),
                end_date=_date(item["end_date"]),
                stability=IncomeStability(item["stability"]),
            )

        for item in _load("obligations.json"):
            self._obligation_use_case.execute(
                profile_id=profile_id,
                description=item["description"],
                amount=_money(item["amount"]),
                category=item["category"],
                frequency=Recurrence(item["frequency"]),
                due_day=item["due_day"],
                start_date=_date(item["start_date"]),
                end_date=_date(item["end_date"]),
                essential=item["essential"],
                debt_related=item["debt_related"],
            )

        for item in _load("debts.json"):
            self._debt_use_case.execute(
                profile_id=profile_id,
                description=item["description"],
                outstanding_balance=_money(item["outstanding_balance"]),
                installment_amount=_money(item["installment_amount"]),
                remaining_installments=item["remaining_installments"],
                interest_rate_optional=item["interest_rate_optional"],
                due_day=item["due_day"],
            )

        for item in _load("goals.json"):
            self._goal_use_case.execute(
                profile_id=profile_id,
                description=item["description"],
                target_amount=_money(item["target_amount"]),
                current_amount=_money(item["current_amount"]),
                deadline=_date(item["deadline"]),
                priority=item["priority"],
                monthly_contribution=_money(item["monthly_contribution"]),
            )

        for item in _load("future_events.json"):
            self._event_use_case.execute(
                profile_id=profile_id,
                description=item["description"],
                event_type=item["event_type"],
                amount=_money(item["amount"]),
                event_date=_date(item["date"]),
                recurrence=Recurrence(item["recurrence"]) if item["recurrence"] else None,
                direction=Direction(item["direction"]),
            )

        if self._balance_snapshot_repo is not None:
            for item in _load("balance_snapshots.json"):
                if self._balance_snapshot_repo.get_by_profile_and_period(profile_id, item["period"]) is not None:
                    continue
                self._balance_snapshot_repo.add(
                    BalanceSnapshot(
                        id=str(uuid4()),
                        profile_id=profile_id,
                        period=item["period"],
                        net_balance=_money(item["net_balance"]),
                        created_at=datetime.utcnow(),
                    )
                )
