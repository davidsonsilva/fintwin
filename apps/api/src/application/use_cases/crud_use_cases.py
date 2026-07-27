# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Casos de uso genéricos de leitura/atualização/exclusão, reaproveitados pelos
6 recursos-filho do onboarding (account, income, obligation, debt, goal, event).

A criação continua específica por recurso pois cada entidade tem campos próprios.
"""

from __future__ import annotations

from typing import Any, Optional


class GetUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, entity_id: str) -> Optional[Any]:
        return self._repo.get(entity_id)


class ListByProfileUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, profile_id: str) -> list[Any]:
        return self._repo.list_by_profile(profile_id)


class UpdateUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, entity: Any) -> None:
        self._repo.update(entity)


class DeleteUseCase:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def execute(self, entity_id: str) -> None:
        self._repo.delete(entity_id)
