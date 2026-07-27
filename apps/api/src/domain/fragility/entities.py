# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Entidade FragilityFinding (Spec seções 11 e 15.1) — toda fragilidade requer evidência."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

from src.domain.shared.enums import Severity


@dataclass
class FragilityFinding:
    id: str
    profile_id: str
    code: str
    severity: Severity
    evidence: Mapping[str, Any]
    detected_at: date
    status: str

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("FragilityFinding requer code.")
        if not self.evidence:
            raise ValueError("FragilityFinding requer evidence (nenhuma fragilidade sem evidência).")
