from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.use_cases.fragility_use_cases import DetectFragilitiesUseCase, ListFragilitiesUseCase
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.domain.shared.enums import Severity
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.fragility_repository import SqlAlchemyFragilityRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.interfaces.http.schemas.fragility import FragilityFindingResponse

router = APIRouter(prefix="/api/v1/profiles", tags=["fragility"])


def _get_profile_or_404(profile_id: str, session: Session):
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(profile_repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


@router.post("/{profile_id}/fragilities/detect", response_model=list[FragilityFindingResponse])
def detect_fragilities_endpoint(
    profile_id: str, session: Session = Depends(get_session)
) -> list[FragilityFindingResponse]:
    profile = _get_profile_or_404(profile_id, session)

    use_case = DetectFragilitiesUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        fragility_repo=SqlAlchemyFragilityRepository(session),
    )
    findings = use_case.execute(profile_id, profile.currency, profile.monthly_expense_reduction_capacity)
    return [FragilityFindingResponse.from_domain(finding) for finding in findings]


@router.get("/{profile_id}/fragilities", response_model=list[FragilityFindingResponse])
def list_fragilities_endpoint(
    profile_id: str,
    severity: Optional[str] = Query(default=None),
    code: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> list[FragilityFindingResponse]:
    _get_profile_or_404(profile_id, session)

    use_case = ListFragilitiesUseCase(SqlAlchemyFragilityRepository(session))
    severity_enum = Severity(severity) if severity is not None else None
    findings = use_case.execute(profile_id, severity=severity_enum, code=code, status=status)
    return [FragilityFindingResponse.from_domain(finding) for finding in findings]
