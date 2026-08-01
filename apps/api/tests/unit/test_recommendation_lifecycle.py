"""O ciclo de vida da recomendação, exercitado de ponta a ponta.

    insight detectado -> recomendação registrada -> usuário analisa
    -> aprova ou rejeita -> plano preventivo criado -> card busca a próxima

Os repositórios são fakes em memória: o que está sob teste é a regra, não o
SQLAlchemy (esse é coberto pelos testes de integração).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import pytest

from src.application.use_cases.recommendation_use_cases import (
    DecideRecommendationUseCase,
    DetectRecommendationUseCase,
    GetInsightUseCase,
    ListRecommendationsUseCase,
    RegisterConversationRecommendationUseCase,
)
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import FinancialObligation, IncomeSource
from src.domain.recommendations import lifecycle
from src.domain.recommendations.entities import (
    Recommendation,
    RecommendationKind,
    RecommendationSource,
    RecommendationStatus,
)
from src.domain.shared.enums import IncomeStability, LiquidityType, PlanStatus, Recurrence
from src.domain.shared.money import Money
from src.interfaces.http.schemas.recommendation import OpportunityResultResponse

CURRENCY = "BRL"
PROFILE = "p1"


def _money(value: str) -> Money:
    return Money(Decimal(value), CURRENCY)


# --- Fakes ------------------------------------------------------------------


class FakeListRepo:
    def __init__(self, items=()) -> None:
        self.items = list(items)

    def list_by_profile(self, profile_id: str):
        return list(self.items)


class FakeRecommendationRepo:
    def __init__(self) -> None:
        self.rows: dict[str, Recommendation] = {}

    def add(self, recommendation: Recommendation) -> Recommendation:
        self.rows[recommendation.id] = recommendation
        return recommendation

    def save(self, recommendation: Recommendation) -> Recommendation:
        self.rows[recommendation.id] = recommendation
        return recommendation

    def get(self, recommendation_id: str) -> Optional[Recommendation]:
        return self.rows.get(recommendation_id)

    def get_pending(self, profile_id: str, kind: RecommendationKind) -> Optional[Recommendation]:
        pending = [
            r
            for r in self.rows.values()
            if r.profile_id == profile_id
            and r.kind is kind
            and r.status is RecommendationStatus.PENDING
        ]
        return max(pending, key=lambda r: r.generated_at, default=None)

    def list_approved(self, profile_id: str, kind: RecommendationKind):
        return [
            r
            for r in self.rows.values()
            if r.profile_id == profile_id
            and r.kind is kind
            and r.status is RecommendationStatus.APPROVED
        ]

    def list_by_profile(self, profile_id: str, status=None):
        rows = [r for r in self.rows.values() if r.profile_id == profile_id]
        if status is not None:
            rows = [r for r in rows if r.status is status]
        return sorted(rows, key=lambda r: r.generated_at, reverse=True)


class FakePlanRepo:
    def __init__(self) -> None:
        self.plans = []

    def add(self, plan) -> None:
        self.plans.append(plan)

    def get(self, plan_id):
        return next((p for p in self.plans if p.id == plan_id), None)


# --- Cenário base -----------------------------------------------------------


def _account(balance: str) -> FinancialAccount:
    return FinancialAccount(
        id="acc",
        profile_id=PROFILE,
        description="Reserva",
        balance=_money(balance),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=True,
    )


def _income(amount: str) -> IncomeSource:
    return IncomeSource(
        id="inc",
        profile_id=PROFILE,
        description="Salário",
        amount=_money(amount),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )


def _obligation(amount: str, essential: bool = True, id_: str = "obl") -> FinancialObligation:
    return FinancialObligation(
        id=id_,
        profile_id=PROFILE,
        description="Aluguel",
        amount=_money(amount),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=essential,
        debt_related=False,
    )


def _goal() -> FinancialGoal:
    return FinancialGoal(
        id="goal-1",
        profile_id=PROFILE,
        description="Entrada do apartamento",
        target_amount=_money("60000.00"),
        current_amount=_money("12000.00"),
        deadline=None,
        priority=1,
        monthly_contribution=_money("900.00"),
    )


def _serializer(result):
    return OpportunityResultResponse.from_domain(result).to_payload()


class World:
    """Perfil folgado, com os repositórios que os casos de uso esperam."""

    def __init__(self, **overrides) -> None:
        self.recommendations = FakeRecommendationRepo()
        self.plans = FakePlanRepo()
        data = dict(
            accounts=[_account("20000.00")],
            incomes=[_income("9000.00")],
            obligations=[_obligation("3000.00")],
            debts=[],
            goals=[_goal()],
            events=[],
        )
        data.update(overrides)
        self.repos = dict(
            recommendation_repo=self.recommendations,
            account_repo=FakeListRepo(data["accounts"]),
            income_repo=FakeListRepo(data["incomes"]),
            obligation_repo=FakeListRepo(data["obligations"]),
            debt_repo=FakeListRepo(data["debts"]),
            goal_repo=FakeListRepo(data["goals"]),
            event_repo=FakeListRepo(data["events"]),
            plan_repo=self.plans,
        )

    def detect(self, custom_pct=None):
        return DetectRecommendationUseCase(serializer=_serializer, **self.repos).execute(
            PROFILE, CURRENCY, custom_pct
        )

    def insight(self):
        return GetInsightUseCase(serializer=_serializer, **self.repos).execute(PROFILE, CURRENCY)

    def decide(self, rec_id, approve, scenario=None):
        return DecideRecommendationUseCase(**self.repos).execute(
            rec_id, CURRENCY, approve, scenario
        )

    def registry(self, status=None):
        return ListRecommendationsUseCase(self.recommendations).execute(PROFILE, status)

    def change_data(self):
        """Muda um dado que o motor lê, invalidando a impressão digital."""
        self.repos["obligation_repo"] = FakeListRepo(
            [_obligation("3000.00"), _obligation("250.00", essential=False, id_="obl2")]
        )


# --- O ciclo ----------------------------------------------------------------


def test_ciclo_completo_ate_o_plano_preventivo() -> None:
    world = World()

    # 1. insight detectado -> recomendação registrada
    surface = world.detect()
    rec = surface.recommendation
    assert rec is not None
    assert rec.status is RecommendationStatus.PENDING
    assert rec.source is RecommendationSource.ENGINE

    # 2. o card mostra essa pendente
    assert world.insight().recommendation.id == rec.id

    # 3. o usuário aprova o cenário que escolheu
    approved = world.decide(rec.id, approve=True, scenario="conservative")
    assert approved.status is RecommendationStatus.APPROVED
    assert approved.selected_scenario == "conservative"
    assert approved.decided_at is not None

    # 4. o plano preventivo nasce vinculado à recomendação
    assert len(world.plans.plans) == 1
    plan = world.plans.plans[0]
    assert plan.id == approved.plan_id
    assert plan.risk_code == lifecycle.GOAL_ACCELERATION_PLAN_CODE
    assert plan.status is PlanStatus.APPROVED
    assert "Entrada do apartamento" in plan.actions[0]["description"]

    # 5. o card NÃO fica exibindo o plano aprovado: procura a próxima ação
    depois = world.insight()
    assert depois.recommendation is None
    assert depois.diagnosis is not None

    # 6. e a recomendação continua no registro, com o desfecho
    registro = world.registry()
    assert [r.status for r in registro] == [RecommendationStatus.APPROVED]


def test_rejeitar_tambem_libera_o_card_e_fica_no_registro() -> None:
    world = World()
    rec = world.detect().recommendation

    rejected = world.decide(rec.id, approve=False)
    assert rejected.status is RecommendationStatus.REJECTED
    assert rejected.selected_scenario is None
    assert world.plans.plans == []

    assert world.insight().recommendation is None
    assert world.registry(RecommendationStatus.REJECTED)[0].id == rec.id


def test_aprovar_sem_escolher_cenario_usa_o_recomendado() -> None:
    world = World()
    rec = world.detect().recommendation
    approved = world.decide(rec.id, approve=True)
    assert approved.selected_scenario == "recommended"


# --- Versionamento ----------------------------------------------------------


def test_detectar_de_novo_com_os_mesmos_dados_nao_duplica() -> None:
    world = World()
    primeira = world.detect().recommendation
    segunda = world.detect().recommendation
    assert primeira.id == segunda.id
    assert len(world.registry()) == 1


def test_dados_novos_criam_versao_ligada_a_anterior() -> None:
    world = World()
    primeira = world.detect().recommendation

    world.change_data()
    segunda = world.detect().recommendation

    assert segunda.id != primeira.id
    assert segunda.supersedes_id == primeira.id
    assert world.recommendations.get(primeira.id).status is RecommendationStatus.SUPERSEDED
    assert world.recommendations.get(primeira.id).superseded_by_id == segunda.id
    # Nada foi sobrescrito: as duas versões continuam no registro.
    assert len(world.registry()) == 2


def test_quando_deixa_de_haver_oportunidade_a_pendente_expira() -> None:
    world = World()
    pendente = world.detect().recommendation

    # Reserva despenca: o portão de segurança fecha.
    world.repos["account_repo"] = FakeListRepo([_account("3000.00")])
    surface = world.detect()

    assert surface.recommendation is None
    assert world.recommendations.get(pendente.id).status is RecommendationStatus.EXPIRED
    assert world.registry(RecommendationStatus.EXPIRED)[0].id == pendente.id


# --- Proteções --------------------------------------------------------------


def test_nao_se_decide_duas_vezes_a_mesma_recomendacao() -> None:
    world = World()
    rec = world.detect().recommendation
    world.decide(rec.id, approve=True)

    with pytest.raises(lifecycle.InvalidTransitionError):
        world.decide(rec.id, approve=False)


def test_nao_se_aprova_recomendacao_defasada() -> None:
    world = World()
    rec = world.detect().recommendation
    world.change_data()

    assert world.insight().stale is True
    with pytest.raises(lifecycle.StaleRecommendationError):
        world.decide(rec.id, approve=True, scenario="recommended")
    assert world.plans.plans == []


def test_insight_sem_pendente_traz_o_diagnostico_para_o_card_explicar() -> None:
    world = World(incomes=[], goals=[])
    surface = world.insight()
    assert surface.recommendation is None
    assert surface.diagnosis["status"] == "insufficient_data"
    assert surface.diagnosis["missing_data"]


def test_conversa_so_vira_registro_por_gesto_explicito() -> None:
    world = World()
    # Ler o insight ou detectar não cria nada vindo de conversa.
    world.detect()
    assert all(r.source is RecommendationSource.ENGINE for r in world.registry())

    saved = RegisterConversationRecommendationUseCase(**world.repos).execute(
        profile_id=PROFILE,
        currency=CURRENCY,
        conversation_id="conv-1",
        message_id="msg-9",
        payload={"status": "available", "summary": "Antecipar a meta com a sobra do 13º"},
    )
    assert saved.source is RecommendationSource.CONVERSATION
    assert saved.conversation_id == "conv-1"
    assert saved.message_id == "msg-9"
    assert saved.status is RecommendationStatus.PENDING
    assert saved.kind is RecommendationKind.CONVERSATION_ADVICE


def test_plano_registra_o_compromisso_do_cenario_escolhido() -> None:
    world = World()
    rec = world.detect().recommendation
    acelerado = next(s for s in rec.payload["scenarios"] if s["key"] == "accelerated")

    world.decide(rec.id, approve=True, scenario="accelerated")
    action = world.plans.plans[0].actions[0]

    assert action["expected_monthly_impact"]["amount"] == acelerado["additional_amount"]["amount"]
    assert action["due_date"].startswith(acelerado["projected_completion"])


def test_transicoes_invalidas_sao_barradas_no_dominio() -> None:
    rec = Recommendation(
        id="r1",
        profile_id=PROFILE,
        kind=RecommendationKind.GOAL_ACCELERATION,
        source=RecommendationSource.ENGINE,
        status=RecommendationStatus.APPROVED,
        generated_at=datetime(2026, 8, 1),
        payload={},
        input_fingerprint="abc",
    )
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.supersede(rec, "r2")
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.expire(rec)


def test_plano_ativo_impede_recomendar_a_mesma_coisa_de_novo() -> None:
    """Aprovar não move dinheiro, então os dados de entrada não mudam.

    Sem esta guarda o motor recomendaria eternamente a mesma oportunidade e o
    card entraria em loop, oferecendo o que o usuário já aprovou.
    """
    world = World()
    rec = world.detect().recommendation
    world.decide(rec.id, approve=True, scenario="recommended")

    surface = world.detect()
    assert surface.recommendation is None
    assert surface.active_plan_id == world.plans.plans[0].id
    # Nenhuma recomendação nova foi criada.
    assert len(world.registry()) == 1

    # O card sabe que há plano em execução e segue monitorando.
    insight = world.insight()
    assert insight.recommendation is None
    assert insight.active_plan_id == world.plans.plans[0].id


def test_plano_cancelado_libera_o_assunto_de_novo() -> None:
    from dataclasses import replace

    world = World()
    rec = world.detect().recommendation
    world.decide(rec.id, approve=True, scenario="recommended")

    world.plans.plans[0] = replace(world.plans.plans[0], status=PlanStatus.CANCELLED)

    surface = world.detect()
    assert surface.recommendation is not None
    assert surface.recommendation.id != rec.id
