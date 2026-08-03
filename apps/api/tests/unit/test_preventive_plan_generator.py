from datetime import date, timedelta
from decimal import Decimal

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.fragility.detector import detect_fragilities
from src.domain.fragility.entities import FragilityFinding
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.preventive_plans.entities import PreventivePlan
from src.domain.preventive_plans.generator import generate_preventive_plans
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, PlanStatus, Recurrence
from src.domain.shared.money import Money

CURRENCY = "BRL"
TODAY = date(2026, 7, 1)
PROFILE_ID = "profile-1"


def _account(balance: str, eligible: bool = True) -> FinancialAccount:
    return FinancialAccount(
        id="acc",
        profile_id=PROFILE_ID,
        description="Conta",
        balance=Money(Decimal(balance), CURRENCY),
        liquidity_type=LiquidityType.EMERGENCY_FUND if eligible else LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=eligible,
    )


def _income(amount: str, description: str = "Renda", frequency: Recurrence = Recurrence.MONTHLY) -> IncomeSource:
    return IncomeSource(
        id=f"income-{description}",
        profile_id=PROFILE_ID,
        description=description,
        amount=Money(Decimal(amount), CURRENCY),
        frequency=frequency,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )


def _obligation(
    amount: str,
    essential: bool = True,
    debt_related: bool = False,
    due_day: int = 5,
    frequency: Recurrence = Recurrence.MONTHLY,
    description: str = "Obrigação",
) -> FinancialObligation:
    return FinancialObligation(
        id=f"obl-{description}",
        profile_id=PROFILE_ID,
        description=description,
        amount=Money(Decimal(amount), CURRENCY),
        category="geral",
        frequency=frequency,
        due_day=due_day,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=essential,
        debt_related=debt_related,
    )


def _debt(installment: str, remaining: int = 12, due_day: int = 10, description: str = "Dívida") -> Debt:
    return Debt(
        id=f"debt-{description}",
        profile_id=PROFILE_ID,
        description=description,
        outstanding_balance=Money(Decimal("10000.00"), CURRENCY),
        installment_amount=Money(Decimal(installment), CURRENCY),
        remaining_installments=remaining,
        interest_rate_optional=None,
        due_day=due_day,
    )


def _goal(contribution: str, priority: int = 1, description: str = "Meta") -> FinancialGoal:
    return FinancialGoal(
        id=f"goal-{description}",
        profile_id=PROFILE_ID,
        description=description,
        target_amount=Money(Decimal("10000.00"), CURRENCY),
        current_amount=Money(Decimal("1000.00"), CURRENCY),
        deadline=None,
        priority=priority,
        monthly_contribution=Money(Decimal(contribution), CURRENCY),
    )


def _event(
    amount: str,
    event_date: date,
    direction: Direction = Direction.EXPENSE,
    recurrence=None,
    description: str = "Evento",
) -> FinancialEvent:
    return FinancialEvent(
        id=f"event-{description}",
        profile_id=PROFILE_ID,
        description=description,
        event_type="tax",
        amount=Money(Decimal(amount), CURRENCY),
        date=event_date,
        recurrence=recurrence,
        direction=direction,
    )


def _generate(
    accounts=None,
    incomes=None,
    obligations=None,
    debts=None,
    goals=None,
    events=None,
    existing_plans=None,
) -> list[PreventivePlan]:
    accounts = accounts or []
    incomes = incomes or []
    obligations = obligations or []
    debts = debts or []
    goals = goals or []
    events = events or []

    from src.domain.autonomy.engine import calculate_autonomy
    from src.domain.projection.engine import project_cashflow
    from src.domain.projection.scenario import ScenarioParameters

    projection = project_cashflow(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        horizon_months=3,
        scenario=ScenarioParameters.probable(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )
    autonomy = calculate_autonomy(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=CURRENCY,
        expense_reduction_capacity=None,
        today=TODAY,
    )
    detected = detect_fragilities(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=CURRENCY,
        projection=projection,
        autonomy=autonomy,
    )
    findings = [
        FragilityFinding(
            id=f"finding-{item.code}",
            profile_id=PROFILE_ID,
            code=item.code,
            severity=item.severity,
            evidence=item.evidence,
            detected_at=TODAY,
            status="active",
        )
        for item in detected
    ]
    return generate_preventive_plans(
        findings=findings,
        existing_plans=existing_plans or [],
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=CURRENCY,
        today=TODAY,
    )


def _plan_for(plans: list[PreventivePlan], risk_code: str) -> PreventivePlan:
    matches = [plan for plan in plans if plan.risk_code == risk_code]
    assert len(matches) == 1, f"esperava exatamente 1 plano para {risk_code}, achou {len(matches)}"
    return matches[0]


def _impact_amount(plan: PreventivePlan, index: int = 0) -> Decimal:
    impact = plan.actions[index]["expected_monthly_impact"]
    assert impact is not None, "esperava expected_monthly_impact preenchido"
    assert impact["currency"] == CURRENCY
    return Decimal(impact["amount"])


def test_income_concentration_generates_qualitative_action() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("9000.00", description="Principal"), _income("500.00", description="Extra")],
    )
    plan = _plan_for(plans, "INCOME_CONCENTRATION")
    assert plan.status == PlanStatus.PROPOSED
    assert plan.actions[0]["expected_monthly_impact"] is None
    assert plan.expected_result["deficit_avoided"] is False
    assert plan.expected_result["autonomy_change_months"] is None


def test_essential_expense_ratio_action_amount_brings_ratio_to_sixty_percent() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[_obligation("2500.00", essential=True)],
    )
    plan = _plan_for(plans, "ESSENTIAL_EXPENSE_RATIO")
    # essential=2500, target=0.60*3000=1800 -> needed=700
    assert _impact_amount(plan) == Decimal("700.00")
    assert plan.expected_result["deficit_avoided"] is False
    # autonomy_change = 700 / 2500 = 0.28 -> arredondado 1 casa = 0.3
    assert plan.expected_result["autonomy_change_months"] == "0.3"


def test_debt_service_ratio_action_amount_brings_ratio_to_thirty_percent() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("500.00", essential=True)],
        debts=[_debt("1500.00", remaining=6)],
    )
    plan = _plan_for(plans, "DEBT_SERVICE_RATIO")
    # debt_service=1500, target=0.30*4000=1200 -> needed=300
    assert _impact_amount(plan) == Decimal("300.00")
    assert plan.expected_result["autonomy_change_months"] is None


def test_recurring_credit_for_essentials_lists_obligations_from_evidence() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("500.00", essential=True, debt_related=True, description="Cartão consignado")],
    )
    plan = _plan_for(plans, "RECURRING_CREDIT_FOR_ESSENTIALS")
    assert "Cartão consignado" in plan.actions[0]["description"]
    assert plan.actions[0]["expected_monthly_impact"] is None


def test_projected_reserve_decline_action_amount_is_average_monthly_shortfall() -> None:
    plans = _generate(
        accounts=[_account("5000.00")],
        incomes=[_income("1000.00")],
        obligations=[_obligation("3000.00", essential=True)],
    )
    plan = _plan_for(plans, "PROJECTED_RESERVE_DECLINE")
    # net_cashflow = 1000 - 3000 = -2000 por mês, 3 meses -> média 2000
    assert _impact_amount(plan) == Decimal("2000.00")
    assert plan.expected_result["deficit_avoided"] is True


def test_concentrated_due_dates_lists_items_and_window() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("6000.00")],
        obligations=[
            _obligation("500.00", essential=True, due_day=5, description="Aluguel"),
            _obligation("300.00", essential=True, due_day=7, description="Água"),
            _obligation("200.00", essential=True, due_day=10, description="Luz"),
        ],
    )
    plan = _plan_for(plans, "CONCENTRATED_DUE_DATES")
    description = plan.actions[0]["description"]
    assert "Aluguel" in description and "Água" in description and "Luz" in description
    assert plan.actions[0]["expected_monthly_impact"] is None


def test_projected_deficit_90_days_uses_lowest_balance_and_first_deficit_period() -> None:
    plans = _generate(
        accounts=[_account("100.00")],
        incomes=[_income("500.00")],
        obligations=[_obligation("3000.00", essential=True)],
    )
    plan = _plan_for(plans, "PROJECTED_DEFICIT_90_DAYS")
    impact = _impact_amount(plan)
    assert impact > 0
    assert plan.expected_result["deficit_avoided"] is True
    assert plan.actions[0]["due_date"] == "2026-07-01"


def test_reserve_below_three_months_action_amount_targets_three_months() -> None:
    plans = _generate(
        accounts=[_account("2000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True)],
    )
    plan = _plan_for(plans, "RESERVE_BELOW_THREE_MONTHS")
    assert _impact_amount(plan) > 0
    assert plan.expected_result["deficit_avoided"] is True
    assert plan.expected_result["autonomy_change_months"] is not None


def test_reserve_below_three_months_rounds_up_so_three_installments_cover_the_gap() -> None:
    # essential=1000.01, basic_autonomy=1 mês (1000.01/1000.01) -> shortfall=2 meses
    # -> total_gap=2000.02, que não divide exatamente por 3 (regressão de um finding
    # real do Meta Harness: 3 parcelas arredondadas para baixo somavam menos que o gap).
    plans = _generate(
        accounts=[_account("1000.01")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("1000.01", essential=True)],
    )
    plan = _plan_for(plans, "RESERVE_BELOW_THREE_MONTHS")
    monthly_impact = _impact_amount(plan)
    assert monthly_impact * Decimal("3") >= Decimal("2000.02")


def test_unprovisioned_annual_expense_action_amount_is_annual_total_over_twelve() -> None:
    plans = _generate(
        accounts=[_account("30000.00")],
        incomes=[_income("8000.00")],
        obligations=[
            _obligation("2000.00", essential=True),
            _obligation("1200.00", essential=True, frequency=Recurrence.YEARLY, description="IPTU"),
        ],
    )
    plan = _plan_for(plans, "UNPROVISIONED_ANNUAL_EXPENSE")
    assert _impact_amount(plan) == Decimal("100.00")


def test_uncovered_future_installments_action_amount_is_excess_over_disposable() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[_obligation("2500.00", essential=True)],
        debts=[_debt("1000.00", remaining=6)],
    )
    plan = _plan_for(plans, "UNCOVERED_FUTURE_INSTALLMENTS")
    # debt_service=1000, disposable=3000-2500=500 -> excess=500
    assert _impact_amount(plan) == Decimal("500.00")
    assert plan.expected_result["deficit_avoided"] is True


def test_incompatible_goal_action_amount_is_gap_over_disposable() -> None:
    plans = _generate(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[_obligation("2500.00", essential=True)],
        goals=[_goal("600.00", priority=1)],
    )
    plan = _plan_for(plans, "INCOMPATIBLE_GOAL")
    # disposable=3000-2500=500, contribution=600 -> gap=100
    assert _impact_amount(plan) == Decimal("100.00")


def test_does_not_duplicate_plan_for_risk_code_with_non_terminal_existing_plan() -> None:
    accounts = [_account("10000.00")]
    incomes = [_income("9000.00", description="Principal"), _income("500.00", description="Extra")]
    first_round = _generate(accounts=accounts, incomes=incomes)
    existing = _plan_for(first_round, "INCOME_CONCENTRATION")

    second_round = _generate(accounts=accounts, incomes=incomes, existing_plans=[existing])
    assert "INCOME_CONCENTRATION" not in {plan.risk_code for plan in second_round}


def test_regenerates_plan_for_risk_code_whose_existing_plan_is_terminal() -> None:
    accounts = [_account("10000.00")]
    incomes = [_income("9000.00", description="Principal"), _income("500.00", description="Extra")]
    first_round = _generate(accounts=accounts, incomes=incomes)
    existing = _plan_for(first_round, "INCOME_CONCENTRATION")
    rejected = PreventivePlan(
        id=existing.id,
        profile_id=existing.profile_id,
        risk_code=existing.risk_code,
        status=PlanStatus.REJECTED,
        actions=existing.actions,
        expected_result=existing.expected_result,
        created_at=existing.created_at,
        approved_at=None,
    )

    second_round = _generate(accounts=accounts, incomes=incomes, existing_plans=[rejected])
    assert "INCOME_CONCENTRATION" in {plan.risk_code for plan in second_round}


def test_nenhuma_descricao_gerada_vaza_representacao_de_desenvolvedor() -> None:
    """Rede sobre os templates, não só sobre o perfil de demonstração.

    O cenário abaixo dispara vários templates de uma vez, incluindo o de
    déficit projetado — que escapou da primeira correção porque o perfil de
    demonstração não o aciona.
    """
    import re

    plans = _generate(
        accounts=[_account("100.00")],
        incomes=[_income("500.00")],
        obligations=[_obligation("3000.00", essential=True)],
    )
    assert plans

    for plan in plans:
        for action in plan.actions:
            texto = action["description"]
            assert not re.search(r"\d\s*(BRL|USD|EUR)\b", texto), texto
            assert not re.search(r"\d{4}-\d{2}-\d{2}", texto), texto
