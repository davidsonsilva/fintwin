# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.balance_history.entities import BalanceSnapshot
from src.domain.shared.money import Money
from src.infrastructure.persistence.models import BalanceSnapshotModel


def _to_model(snapshot: BalanceSnapshot) -> BalanceSnapshotModel:
    return BalanceSnapshotModel(
        id=snapshot.id,
        profile_id=snapshot.profile_id,
        period=snapshot.period,
        net_balance_amount=snapshot.net_balance.amount,
        net_balance_currency=snapshot.net_balance.currency,
        created_at=snapshot.created_at,
    )


def _to_entity(model: BalanceSnapshotModel) -> BalanceSnapshot:
    return BalanceSnapshot(
        id=model.id,
        profile_id=model.profile_id,
        period=model.period,
        net_balance=Money(Decimal(str(model.net_balance_amount)), model.net_balance_currency),
        created_at=model.created_at,
    )


class SqlAlchemyBalanceSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, snapshot: BalanceSnapshot) -> None:
        self._session.add(_to_model(snapshot))
        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            # Só engolimos o erro se for de fato a corrida esperada (outra requisição já
            # gravou o snapshot deste profile_id/period antes de nós). Qualquer outra causa
            # de IntegrityError (ex.: FK para um perfil excluído) é propagada normalmente —
            # checar a mensagem do driver seria específico de banco (sqlite vs. postgres),
            # então revalidamos consultando o estado real em vez disso.
            if self.get_by_profile_and_period(snapshot.profile_id, snapshot.period) is None:
                raise

    def get_by_profile_and_period(self, profile_id: str, period: str) -> Optional[BalanceSnapshot]:
        stmt = select(BalanceSnapshotModel).where(
            BalanceSnapshotModel.profile_id == profile_id,
            BalanceSnapshotModel.period == period,
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    def list_by_profile_ordered(self, profile_id: str, limit: int) -> list[BalanceSnapshot]:
        stmt = (
            select(BalanceSnapshotModel)
            .where(BalanceSnapshotModel.profile_id == profile_id)
            .order_by(BalanceSnapshotModel.period.desc())
            .limit(limit)
        )
        models = self._session.execute(stmt).scalars().all()
        snapshots = [_to_entity(model) for model in models]
        return list(reversed(snapshots))
