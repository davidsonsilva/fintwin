from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel

from src.domain.fragility.entities import FragilityFinding
from src.domain.fragility.rules import RULES


class FragilityFindingResponse(BaseModel):
    id: str
    profile_id: str
    code: str
    title: str
    description: str
    formula: str
    threshold: str
    severity: str
    evidence: dict[str, Any]
    detected_at: date
    status: str

    @classmethod
    def from_domain(cls, finding: FragilityFinding) -> "FragilityFindingResponse":
        rule = RULES[finding.code]
        return cls(
            id=finding.id,
            profile_id=finding.profile_id,
            code=finding.code,
            title=rule.title,
            description=rule.description,
            formula=rule.formula,
            threshold=rule.threshold,
            severity=finding.severity.value,
            evidence=dict(finding.evidence),
            detected_at=finding.detected_at,
            status=finding.status,
        )
