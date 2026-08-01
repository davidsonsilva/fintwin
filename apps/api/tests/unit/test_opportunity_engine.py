from datetime import date
from decimal import Decimal

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.opportunity.engine import analyze_opportunity
from src.domain.opportunity.entities import OpportunityStatus, ScenarioKey
from src.domain.opportunity.fingerprint import compute_input_fingerprint
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money

CURRENCY = "BRL"
TODAY = date(2026, 8, 1)


def _money(value: str) -> Money:
    return Money(Decimal(value), CURRENCY)


def _account(balance: str, eligible: bool = True, id_: str = "acc") -> FinancialAccount:
    return FinancialAccount(
        id=id_,
        profile_id="p1",
        description="Reserva",
        balance=_money(balance),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=eligible,
    )


def _income(amount: str, stability: IncomeStability = IncomeStability.STABLE) -> IncomeSource:
    return IncomeSource(
        id="inc",
        profile_id="p1",
        description="Salário",
        amount=_money(amount),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=stability,
    )


def _obligation(
    amount: str, essential: bool, category: str = "moradia", id_: str = "obl"
) -> FinancialObligation:
    return FinancialObligation(
        id=id_,
        profile_id="p1",
        description="Despesa",
        amount=_money(amount),
        category=category,
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=essential,
        debt_related=False,
    )


def _goal(
    target: str = "60000.00",
    current: str = "12000.00",
    contribution: str = "900.00",
    priority: int = 1,
    id_: str = "goal-1",
) -> FinancialGoal:
    return FinancialGoal(
        id=id_,
        profile_id="p1",
        description="Entrada do apartamento",
        target_amount=_money(target),
        current_amount=_money(current),
        deadline=None,
        priority=priority,
        monthly_contribution=_money(contribution),
    )


def _healthy(**overrides):
    """Perfil folgado: renda 9.000, essenciais 3.000, reserva 6 meses."""
    base = dict(
        accounts=[_account("20000.00")],
        incomes=[_income("9000.00")],
        obligations=[_obligation("3000.00", essential=True), _obligation("800.00", essential=False, category="lazer")],
        debts=[],
        goals=[_goal()],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )
    base.update(overrides)
    return base


# --- Dados insuficientes ----------------------------------------------------


def test_sem_renda_devolve_dados_insuficientes() -> None:
    result = analyze_opportunity(**_healthy(incomes=[]))
    assert result.status is OpportunityStatus.INSUFFICIENT_DATA
    assert any("renda" in item.lower() for item in result.missing_data)
    assert result.recommended is None


def test_sem_meta_devolve_dados_insuficientes() -> None:
    result = analyze_opportunity(**_healthy(goals=[]))
    assert result.status is OpportunityStatus.INSUFFICIENT_DATA
    assert any("meta" in item.lower() for item in result.missing_data)


# --- Portões de segurança ---------------------------------------------------


def test_reserva_abaixo_do_piso_bloqueia_a_recomendacao() -> None:
    # 3.000 de essenciais com 6.000 de reserva = 2 meses, abaixo do piso de 3.
    result = analyze_opportunity(**_healthy(accounts=[_account("6000.00")]))
    assert result.status is OpportunityStatus.NO_ACTION
    assert "reserva" in result.reason.lower()
    # Mesmo sem recomendar, o diagnóstico completo continua disponível.
    assert result.reserve_months == Decimal("2.0")
    assert result.evidence


def test_essenciais_acima_do_teto_bloqueiam_a_recomendacao() -> None:
    result = analyze_opportunity(
        **_healthy(
            accounts=[_account("40000.00")],
            obligations=[_obligation("6000.00", essential=True)],
            goals=[_goal(contribution="100.00")],
        )
    )
    assert result.status is OpportunityStatus.NO_ACTION
    assert "essenciais" in result.reason.lower()


def test_sem_sobra_recorrente_nao_recomenda() -> None:
    result = analyze_opportunity(
        **_healthy(
            obligations=[
                _obligation("3000.00", essential=True),
                _obligation("5100.00", essential=False, category="lazer", id_="obl2"),
            ]
        )
    )
    assert result.status is OpportunityStatus.NO_ACTION
    assert "sobra recorrente" in result.reason.lower()


def test_meta_ja_atingida_nao_recomenda() -> None:
    result = analyze_opportunity(**_healthy(goals=[_goal(target="10000.00", current="10000.00")]))
    assert result.status is OpportunityStatus.NO_ACTION
    assert "já foi atingida" in result.reason


# --- Recomendação disponível ------------------------------------------------


def test_recomendacao_sai_da_sobra_real_e_nao_de_valor_fixo() -> None:
    result = analyze_opportunity(**_healthy())
    assert result.status is OpportunityStatus.AVAILABLE

    # sobra = 9000 - 3800 (obrigações) - 900 (aporte) = 4300
    assert result.recurring_surplus == _money("4300.00")
    # 60% de 4300 = 2580 -> 28,6% da renda -> teto de 15%
    assert result.recommended.additional_pct.as_fraction() == Decimal("0.15")
    assert result.recommended.additional_amount == _money("1350.00")
    assert result.recommended.new_monthly_contribution == _money("2250.00")


def test_percentual_acompanha_a_sobra_quando_ela_e_menor_que_o_teto() -> None:
    # sobra = 9000 - 3000 - 4500 - 900 = 600 -> 60% = 360 -> 4% da renda
    result = analyze_opportunity(
        **_healthy(
            obligations=[
                _obligation("3000.00", essential=True),
                _obligation("4500.00", essential=False, category="lazer", id_="obl2"),
            ]
        )
    )
    assert result.status is OpportunityStatus.AVAILABLE
    assert result.recommended.additional_pct.as_fraction() == Decimal("0.04")
    assert result.recommended.additional_amount == _money("360.00")


def test_meta_e_antecipada_e_o_prazo_vem_do_calculo() -> None:
    result = analyze_opportunity(**_healthy())
    # faltam 48.000; com 900/mês = 54 meses, com 2.250/mês = 22 meses
    assert result.baseline_months_to_goal == Decimal("54")
    assert result.recommended.months_to_goal == Decimal("22")
    assert result.recommended.months_saved == Decimal("32")
    assert result.recommended.projected_completion == "2028-06"


def test_tres_cenarios_ordenados_por_agressividade() -> None:
    result = analyze_opportunity(
        **_healthy(
            obligations=[
                _obligation("3000.00", essential=True),
                _obligation("4500.00", essential=False, category="lazer", id_="obl2"),
            ]
        )
    )
    by_key = {s.key: s for s in result.scenarios}
    assert set(by_key) == {ScenarioKey.CONSERVATIVE, ScenarioKey.RECOMMENDED, ScenarioKey.ACCELERATED}
    assert (
        by_key[ScenarioKey.CONSERVATIVE].additional_pct.as_fraction()
        < by_key[ScenarioKey.RECOMMENDED].additional_pct.as_fraction()
        < by_key[ScenarioKey.ACCELERATED].additional_pct.as_fraction()
    )


def test_nenhum_cenario_ultrapassa_a_sobra_recorrente() -> None:
    result = analyze_opportunity(**_healthy())
    for scenario in result.scenarios:
        assert scenario.monthly_surplus_after.amount >= 0


def test_origem_do_dinheiro_nunca_e_despesa_essencial() -> None:
    result = analyze_opportunity(**_healthy())
    assert result.funding_sources
    assert all(not source.essential for source in result.funding_sources)
    assert any("lazer" in source.label for source in result.funding_sources)


def test_riscos_incluem_renda_variavel_e_o_aviso_de_nao_movimentar_dinheiro() -> None:
    result = analyze_opportunity(
        **_healthy(incomes=[_income("9000.00", stability=IncomeStability.VARIABLE)])
    )
    assert any("variável" in risk for risk in result.risks)
    assert any("não movimenta dinheiro" in risk for risk in result.risks)


def test_evento_futuro_de_saida_entra_como_risco() -> None:
    event = FinancialEvent(
        id="ev1",
        profile_id="p1",
        description="IPVA",
        event_type="tax",
        amount=_money("2400.00"),
        date=date(2026, 10, 10),
        recurrence=None,
        direction=Direction.EXPENSE,
    )
    result = analyze_opportunity(**_healthy(events=[event]))
    assert any("IPVA" in risk for risk in result.risks)


def test_cenario_customizado_entra_com_os_mesmos_calculos() -> None:
    result = analyze_opportunity(**_healthy(), custom_pct=Decimal("0.03"))
    custom = next(s for s in result.scenarios if s.key is ScenarioKey.CUSTOM)
    assert custom.additional_pct.as_fraction() == Decimal("0.03")
    assert custom.additional_amount == _money("270.00")


def test_premissas_sao_sempre_declaradas() -> None:
    result = analyze_opportunity(**_healthy())
    assert len(result.assumptions) >= 5
    assert any("Sobra recorrente" in item for item in result.assumptions)


def test_motor_e_deterministico() -> None:
    first = analyze_opportunity(**_healthy())
    second = analyze_opportunity(**_healthy())
    assert first.recommended.additional_amount == second.recommended.additional_amount
    assert first.recommended.months_to_goal == second.recommended.months_to_goal


# --- Impressão digital ------------------------------------------------------


def test_fingerprint_muda_quando_um_dado_relevante_muda() -> None:
    args = dict(
        accounts=[_account("20000.00")],
        incomes=[_income("9000.00")],
        obligations=[_obligation("3000.00", essential=True)],
        debts=[],
        goals=[_goal()],
        events=[],
        currency=CURRENCY,
    )
    before = compute_input_fingerprint(**args)
    assert before == compute_input_fingerprint(**args)

    args["accounts"] = [_account("21000.00")]
    assert compute_input_fingerprint(**args) != before


def test_fingerprint_ignora_ordem_das_listas() -> None:
    a, b = _account("1000.00", id_="a1"), _account("2000.00", id_="a2")
    common = dict(
        incomes=[_income("9000.00")],
        obligations=[_obligation("3000.00", essential=True)],
        debts=[],
        goals=[_goal()],
        events=[],
        currency=CURRENCY,
    )
    assert compute_input_fingerprint(accounts=[a, b], **common) == compute_input_fingerprint(
        accounts=[b, a], **common
    )


def test_debts_entram_na_sobra_recorrente() -> None:
    debt = Debt(
        id="d1",
        profile_id="p1",
        description="Financiamento",
        outstanding_balance=_money("30000.00"),
        installment_amount=_money("1000.00"),
        remaining_installments=30,
        interest_rate_optional=None,
        due_day=10,
    )
    result = analyze_opportunity(**_healthy(debts=[debt]))
    assert result.recurring_surplus == _money("3300.00")
