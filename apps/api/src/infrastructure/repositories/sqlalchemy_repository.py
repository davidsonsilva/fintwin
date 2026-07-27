# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Repositório genérico SQLAlchemy, reaproveitado pelos 6 recursos-filho do onboarding.

Cada recurso concreto (account, income, obligation, debt, goal, event) segue o
mesmo padrão de CRUD por profile_id; sem essa base, seriam 6 implementações
quase idênticas.
"""

from __future__ import annotations

from typing import Callable, Generic, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

TModel = TypeVar("TModel")
TEntity = TypeVar("TEntity")


class SqlAlchemyRepository(Generic[TModel, TEntity]):
    """CRUD genérico por profile_id sobre um model SQLAlchemy.

    `to_model` converte entidade de domínio -> model ORM.
    `to_entity` converte model ORM -> entidade de domínio.
    """

    model: type[TModel]

    def __init__(
        self,
        session: Session,
        to_model: Callable[[TEntity], TModel],
        to_entity: Callable[[TModel], TEntity],
    ) -> None:
        self._session = session
        self._to_model = to_model
        self._to_entity = to_entity

    def add(self, entity: TEntity) -> None:
        self._session.add(self._to_model(entity))
        self._session.commit()

    def get(self, entity_id: str) -> Optional[TEntity]:
        model = self._session.get(self.model, entity_id)
        return self._to_entity(model) if model is not None else None

    def list_by_profile(self, profile_id: str) -> list[TEntity]:
        stmt = select(self.model).where(self.model.profile_id == profile_id)
        models = self._session.execute(stmt).scalars().all()
        return [self._to_entity(model) for model in models]

    def update(self, entity: TEntity) -> None:
        new_model = self._to_model(entity)
        self._session.merge(new_model)
        self._session.commit()

    def delete(self, entity_id: str) -> None:
        model = self._session.get(self.model, entity_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()
