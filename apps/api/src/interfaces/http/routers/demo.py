from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.debt_use_cases import CreateDebtUseCase
from src.application.use_cases.demo_use_cases import LoadDemoProfileUseCase
from src.application.use_cases.event_use_cases import CreateEventUseCase
from src.application.use_cases.goal_use_cases import CreateGoalUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository

router = APIRouter(prefix="/api/v1/profiles", tags=["demo"])


@router.post("/{profile_id}/demo", status_code=204)
def load_demo_profile(profile_id: str, session: Session = Depends(get_session)) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    if GetProfileUseCase(profile_repo).execute(profile_id) is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")

    use_case = LoadDemoProfileUseCase(
        account_use_case=CreateAccountUseCase(SqlAlchemyAccountRepository(session)),
        income_use_case=CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session)),
        obligation_use_case=CreateObligationUseCase(SqlAlchemyObligationRepository(session)),
        debt_use_case=CreateDebtUseCase(SqlAlchemyDebtRepository(session)),
        goal_use_case=CreateGoalUseCase(SqlAlchemyGoalRepository(session)),
        event_use_case=CreateEventUseCase(SqlAlchemyEventRepository(session)),
    )
    use_case.execute(profile_id)
