from decimal import Decimal

from sqlalchemy.orm import Session

from src.application.use_cases.profile_use_cases import (
    CreateProfileUseCase,
    GetProfileUseCase,
    UpdateProfileUseCase,
)
from src.domain.shared.percentage import Percentage
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def test_create_and_get_profile(session: Session) -> None:
    repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(repo).execute(
        currency="BRL", dependents=2, monthly_expense_reduction_capacity=Percentage(Decimal("0.15"))
    )

    fetched = GetProfileUseCase(repo).execute(profile.id)

    assert fetched is not None
    assert fetched.currency == "BRL"
    assert fetched.dependents == 2
    assert fetched.monthly_expense_reduction_capacity.as_fraction() == Decimal("0.15")


def test_update_profile(session: Session) -> None:
    repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )

    profile.dependents = 3
    UpdateProfileUseCase(repo).execute(profile)

    fetched = GetProfileUseCase(repo).execute(profile.id)
    assert fetched is not None
    assert fetched.dependents == 3


def test_get_profile_not_found(session: Session) -> None:
    repo = SqlAlchemyProfileRepository(session)
    assert GetProfileUseCase(repo).execute("does-not-exist") is None
