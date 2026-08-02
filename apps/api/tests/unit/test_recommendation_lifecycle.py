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
    OpportunityActionOutdatedError,
    OpportunityNotFoundError,
    RegisterConversationRecommendationUseCase,
)
from src.domain.agent.entities import AgentMessage, Conversation
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import FinancialObligation, IncomeSource
from src.domain.preventive_plans.entities import PreventivePlan
from src.domain.recommendations import lifecycle
from src.domain.recommendations.entities import (
    Recommendation,
    RecommendationKind,
    RecommendationSource,
    RecommendationStatus,
)
from src.domain.shared.enums import (
    IncomeStability,
    LiquidityType,
    MessageRole,
    PlanStatus,
    Recurrence,
)
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

    def add_for_opportunity(self, recommendation: Recommendation) -> Recommendation:
        """Imita a unicidade do banco: quem chega depois recebe quem venceu."""
        existing = self.get_by_opportunity_id(recommendation.opportunity_id)
        if existing is not None:
            return existing
        return self.add(recommendation)

    def get_by_opportunity_id(self, opportunity_id) -> Optional[Recommendation]:
        if opportunity_id is None:
            return None
        return next(
            (r for r in self.rows.values() if r.opportunity_id == opportunity_id), None
        )

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

    def list_pending(self, profile_id: str):
        return self.list_by_profile(profile_id, RecommendationStatus.PENDING)


class FakePlanRepo:
    def __init__(self) -> None:
        self.plans = []

    def add(self, plan) -> None:
        self.plans.append(plan)

    def get(self, plan_id):
        return next((p for p in self.plans if p.id == plan_id), None)

    def list_by_profile(self, profile_id: str):
        return [p for p in self.plans if p.profile_id == profile_id]


class FakeAgentMessageRepo:
    def __init__(self) -> None:
        self.rows = {}

    def add(self, message):
        self.rows[message.id] = message
        return message

    def get(self, message_id: str):
        return self.rows.get(message_id)


class FakeConversationRepo:
    def __init__(self) -> None:
        self.rows = {}

    def add(self, conversation):
        self.rows[conversation.id] = conversation
        return conversation

    def get(self, conversation_id: str):
        return self.rows.get(conversation_id)


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
        self.conversations = FakeConversationRepo()
        self.messages = FakeAgentMessageRepo()
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

    def answer_with_opportunity(self, topic="income_commitment", subject_key=None):
        """Uma resposta do agente já gravada, com um bloco acionável."""
        self.conversations.add(
            Conversation(
                id="conv-1", profile_id=PROFILE, created_at=datetime(2026, 8, 1), updated_at=datetime(2026, 8, 1)
            )
        )
        self.messages.add(
            AgentMessage(
                id="msg-9",
                conversation_id="conv-1",
                role=MessageRole.ASSISTANT,
                content="Dá para antecipar a meta com a sobra do 13º.",
                opportunities=[
                    {
                        "id": "msg-9-op1",
                        "topic": topic,
                        "subject_key": subject_key,
                        "title": "Antecipar a meta com a sobra do 13º",
                        "diagnosis": "A sobra do 13º pode ir para a meta.",
                        "suggested_actions": ["Direcionar a sobra do 13º para a meta"],
                        "evidence_references": ["ev1"],
                        "assessment": None,
                        "requires_simulation": False,
                        "simulation_status": "not_required",
                        "related_recommendation_id": None,
                        "related_plan_id": None,
                        "available_actions": ["save"],
                    }
                ],
                created_at=datetime(2026, 8, 1),
            )
        )
        return "msg-9-op1"

    def save_opportunity(self, opportunity_id="msg-9-op1"):
        return RegisterConversationRecommendationUseCase(
            agent_message_repo=self.messages, conversation_repo=self.conversations, **self.repos
        ).execute(
            profile_id=PROFILE,
            currency=CURRENCY,
            conversation_id="conv-1",
            message_id="msg-9",
            opportunity_id=opportunity_id,
        )

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

    world.answer_with_opportunity()
    saved = world.save_opportunity()

    assert saved.source is RecommendationSource.CONVERSATION
    assert saved.conversation_id == "conv-1"
    assert saved.message_id == "msg-9"
    assert saved.status is RecommendationStatus.PENDING
    assert saved.kind is RecommendationKind.CONVERSATION_ADVICE
    # O conteúdo veio do bloco gravado, não de nada que o cliente enviou.
    assert saved.payload["topic"] == "income_commitment"
    assert saved.payload["opportunity_id"] == "msg-9-op1"
    assert saved.payload["diagnosis"] == "A sobra do 13º pode ir para a meta."


def test_salvar_oportunidade_ignora_conteudo_do_cliente() -> None:
    """O cliente manda referências; o registro sai do snapshot da mensagem."""
    world = World()
    world.answer_with_opportunity(topic="debt_service", subject_key=None)

    saved = world.save_opportunity()

    assert saved.payload["topic"] == "debt_service"
    assert saved.payload["suggested_actions"] == ["Direcionar a sobra do 13º para a meta"]
    assert saved.payload["evidence_references"] == ["ev1"]


def test_oportunidade_inexistente_na_mensagem_nao_vira_registro() -> None:
    world = World()
    world.answer_with_opportunity()

    with pytest.raises(OpportunityNotFoundError):
        world.save_opportunity("msg-9-op7")
    assert world.registry() == []


def test_salvar_revalida_e_devolve_o_plano_que_surgiu_depois() -> None:
    """`available_actions` é o retrato do que foi exibido, não autorização."""
    world = World()
    world.answer_with_opportunity(topic="goal_acceleration")
    world.plans.add(
        PreventivePlan(
            id="plan-1",
            profile_id=PROFILE,
            risk_code="GOAL_ACCELERATION_OPPORTUNITY",
            status=PlanStatus.APPROVED,
            actions=[{"description": "Aumentar o aporte mensal."}],
            expected_result={},
            created_at=datetime(2026, 8, 2),
            approved_at=datetime(2026, 8, 2),
        )
    )

    with pytest.raises(OpportunityActionOutdatedError) as exc:
        world.save_opportunity()

    assert exc.value.current_action == "view_plan"
    assert exc.value.plan_id == "plan-1"
    assert world.registry() == []


def test_salvar_duas_vezes_devolve_a_recomendacao_ja_registrada() -> None:
    world = World()
    world.answer_with_opportunity()
    primeira = world.save_opportunity()

    with pytest.raises(OpportunityActionOutdatedError) as exc:
        world.save_opportunity()

    assert exc.value.current_action == "view_recommendation"
    assert exc.value.recommendation_id == primeira.id
    assert len(world.registry()) == 1


def test_corrida_de_dois_cliques_nao_cria_dois_registros() -> None:
    """Revalidar em memória não decide a corrida — a unicidade no banco decide.

    Simula as duas requisições passando pela revalidação antes de qualquer
    INSERT confirmar: o repositório é quem barra a segunda.
    """
    world = World()
    world.answer_with_opportunity()
    vencedora = world.save_opportunity()

    perdedora = Recommendation(
        id="outra",
        profile_id=PROFILE,
        kind=RecommendationKind.CONVERSATION_ADVICE,
        source=RecommendationSource.CONVERSATION,
        status=RecommendationStatus.PENDING,
        generated_at=datetime(2026, 8, 1),
        payload={"topic": "income_commitment"},
        input_fingerprint="fp",
        opportunity_id="msg-9-op1",
    )
    gravada = world.recommendations.add_for_opportunity(perdedora)

    assert gravada.id == vencedora.id
    assert len(world.registry()) == 1


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


def test_aprovar_recomendacao_da_conversa_nao_cria_plano() -> None:
    """Sem cenário calculado não há compromisso mensal a acompanhar.

    Forçar um plano aqui exigiria inventar números que o motor nunca produziu.
    """
    world = World()
    world.answer_with_opportunity()
    saved = world.save_opportunity()

    approved = world.decide(saved.id, approve=True)
    assert approved.status is RecommendationStatus.APPROVED
    assert approved.plan_id is None
    assert world.plans.plans == []
