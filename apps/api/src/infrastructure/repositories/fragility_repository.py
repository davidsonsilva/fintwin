# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.domain.fragility.entities import FragilityFinding
from src.infrastructure.persistence.models import FragilityFindingModel
from src.infrastructure.repositories.sqlalchemy_repository import SqlAlchemyRepository


def _to_model(finding: FragilityFinding) -> FragilityFindingModel:
    return FragilityFindingModel(
        id=finding.id,
        profile_id=finding.profile_id,
        code=finding.code,
        severity=finding.severity,
        evidence=dict(finding.evidence),
        detected_at=finding.detected_at,
        status=finding.status,
    )


def _to_entity(model: FragilityFindingModel) -> FragilityFinding:
    return FragilityFinding(
        id=model.id,
        profile_id=model.profile_id,
        code=model.code,
        severity=model.severity,
        evidence=dict(model.evidence),
        detected_at=model.detected_at,
        status=model.status,
    )


class SqlAlchemyFragilityRepository(SqlAlchemyRepository[FragilityFindingModel, FragilityFinding]):
    model = FragilityFindingModel

    def __init__(self, session: Session) -> None:
        super().__init__(session, _to_model, _to_entity)

    def delete_all_by_profile(self, profile_id: str) -> None:
        self._session.execute(delete(FragilityFindingModel).where(FragilityFindingModel.profile_id == profile_id))
        self._session.commit()
