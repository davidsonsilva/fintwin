from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.application.use_cases.expense_breakdown_use_cases import GetExpenseBreakdownByCategoryUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.domain.shared.enums import Recurrence
from src.domain.shared.money import CurrencyMismatchError, Money
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def _create_profile(session: Session) -> str:
    repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    return profile.id


def test_breakdown_groups_by_category_and_sums_percentages_to_one(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyObligationRepository(session)
    CreateObligationUseCase(repo).execute(
        profile_id=profile_id,
        description="Aluguel",
        amount=Money(Decimal("1500.00"), "BRL"),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=True,
        debt_related=False,
    )
    CreateObligationUseCase(repo).execute(
        profile_id=profile_id,
        description="Supermercado",
        amount=Money(Decimal("500.00"), "BRL"),
        category="alimentacao",
        frequency=Recurrence.MONTHLY,
        due_day=10,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=True,
        debt_related=False,
    )

    breakdown = GetExpenseBreakdownByCategoryUseCase(repo).execute(profile_id, "BRL")

    assert len(breakdown) == 2
    assert breakdown[0].category == "moradia"
    assert breakdown[0].amount == Money(Decimal("1500.00"), "BRL")
    assert breakdown[0].percentage.as_fraction() == Decimal("0.75")
    assert breakdown[1].category == "alimentacao"
    assert breakdown[1].percentage.as_fraction() == Decimal("0.25")


def test_breakdown_empty_when_no_obligations(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyObligationRepository(session)

    breakdown = GetExpenseBreakdownByCategoryUseCase(repo).execute(profile_id, "BRL")

    assert breakdown == []


def test_breakdown_rejects_obligation_in_mismatched_currency(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyObligationRepository(session)
    CreateObligationUseCase(repo).execute(
        profile_id=profile_id,
        description="Assinatura internacional",
        amount=Money(Decimal("100.00"), "USD"),
        category="assinaturas",
        frequency=Recurrence.MONTHLY,
        due_day=15,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=False,
        debt_related=False,
    )

    with pytest.raises(CurrencyMismatchError):
        GetExpenseBreakdownByCategoryUseCase(repo).execute(profile_id, "BRL")
