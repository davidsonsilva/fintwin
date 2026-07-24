from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.debt_use_cases import CreateDebtUseCase
from src.application.use_cases.demo_use_cases import LoadDemoProfileUseCase
from src.application.use_cases.event_use_cases import CreateEventUseCase
from src.application.use_cases.goal_use_cases import CreateGoalUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def test_load_demo_profile_persists_all_child_resources(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )

    account_repo = SqlAlchemyAccountRepository(session)
    income_repo = SqlAlchemyIncomeSourceRepository(session)
    obligation_repo = SqlAlchemyObligationRepository(session)
    debt_repo = SqlAlchemyDebtRepository(session)
    goal_repo = SqlAlchemyGoalRepository(session)
    event_repo = SqlAlchemyEventRepository(session)

    use_case = LoadDemoProfileUseCase(
        account_use_case=CreateAccountUseCase(account_repo),
        income_use_case=CreateIncomeSourceUseCase(income_repo),
        obligation_use_case=CreateObligationUseCase(obligation_repo),
        debt_use_case=CreateDebtUseCase(debt_repo),
        goal_use_case=CreateGoalUseCase(goal_repo),
        event_use_case=CreateEventUseCase(event_repo),
    )
    use_case.execute(profile.id)

    assert len(account_repo.list_by_profile(profile.id)) == 2
    assert len(income_repo.list_by_profile(profile.id)) == 1
    assert len(obligation_repo.list_by_profile(profile.id)) == 3
    assert len(debt_repo.list_by_profile(profile.id)) == 1
    assert len(goal_repo.list_by_profile(profile.id)) == 1
    assert len(event_repo.list_by_profile(profile.id)) == 3
