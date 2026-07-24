"""Interface de repositório para FragilityFinding (Spec seção 18.8)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.fragility.entities import FragilityFinding


class FragilityRepository(Protocol):
    def add(self, finding: FragilityFinding) -> None: ...
    def get(self, finding_id: str) -> Optional[FragilityFinding]: ...
    def list_by_profile(self, profile_id: str) -> list[FragilityFinding]: ...
    def delete_all_by_profile(self, profile_id: str) -> None: ...
