"""Uma resposta pode conter várias oportunidades — cada uma um bloco próprio.

O que estes testes protegem: o cliente nunca precisa ler o texto da resposta
para saber o que é acionável, e o backend nunca deixa a IA classificar nada.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from src.application.use_cases.agent_use_cases import SendAgentMessageUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.domain.agent.entities import AgentMessage, Conversation
from src.domain.fragility.entities import FragilityFinding
from src.domain.preventive_plans.entities import PreventivePlan
from src.domain.recommendations.entities import (
    Recommendation,
    RecommendationKind,
    RecommendationSource,
    RecommendationStatus,
)
from src.domain.shared.enums import (
    IncomeStability,
    MessageRole,
    PlanStatus,
    Recurrence,
    Severity,
)
from src.domain.shared.money import Money
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.agent_message_repository import SqlAlchemyAgentMessageRepository
from src.infrastructure.repositories.conversation_repository import SqlAlchemyConversationRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.fragility_repository import SqlAlchemyFragilityRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.preventive_plan_repository import SqlAlchemyPreventivePlanRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.recommendation_repository import SqlAlchemyRecommendationRepository
from src.interfaces.http.schemas.agent import AgentMessageHistoryItem


@dataclass
class FakeBlock:
    type: str
    text: str = ""
    name: str = ""
    input: Optional[dict] = None
    id: str = ""


@dataclass
class FakeResponse:
    content: list


class FakeLLM:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = list(responses)

    def create_message(self, system: str, messages: list, tools: list) -> FakeResponse:
        return self._responses.pop(0)


def _make_use_case(session: Session, llm_client: Any) -> SendAgentMessageUseCase:
    return SendAgentMessageUseCase(
        llm_client=llm_client,
        conversation_repo=SqlAlchemyConversationRepository(session),
        agent_message_repo=SqlAlchemyAgentMessageRepository(session),
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        fragility_repo=SqlAlchemyFragilityRepository(session),
        recommendation_repo=SqlAlchemyRecommendationRepository(session),
        plan_repo=SqlAlchemyPreventivePlanRepository(session),
    )


def _make_profile(session: Session):
    return CreateProfileUseCase(SqlAlchemyProfileRepository(session)).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )


def _with_income_and_obligation(session: Session, profile_id: str) -> None:
    """Renda 5.000 e obrigação 3.000 => comprometimento 0,60 (faixa "atenção")."""
    CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session)).execute(
        profile_id=profile_id,
        description="Salário",
        amount=Money(Decimal("5000.00"), "BRL"),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )
    CreateObligationUseCase(SqlAlchemyObligationRepository(session)).execute(
        profile_id=profile_id,
        description="Aluguel",
        amount=Money(Decimal("3000.00"), "BRL"),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=True,
        debt_related=False,
    )


def _add_finding(session: Session, profile_id: str, code: str, severity: Severity) -> None:
    SqlAlchemyFragilityRepository(session).add(
        FragilityFinding(
            id=str(uuid4()),
            profile_id=profile_id,
            code=code,
            severity=severity,
            evidence={"reserve_months": "1.2"},
            detected_at=date(2026, 8, 1),
            status="open",
        )
    )


def _add_active_plan(session: Session, profile_id: str, risk_code: str) -> str:
    plan = PreventivePlan(
        id=str(uuid4()),
        profile_id=profile_id,
        risk_code=risk_code,
        status=PlanStatus.APPROVED,
        actions=[{"description": "Aumentar o aporte mensal.", "due_date": "2026-12-01"}],
        expected_result={"deficit_avoided": True},
        created_at=datetime(2026, 8, 1),
        approved_at=datetime(2026, 8, 1),
    )
    SqlAlchemyPreventivePlanRepository(session).add(plan)
    return plan.id


def _add_pending_conversation_recommendation(session: Session, profile_id: str, topic: str) -> str:
    recommendation = SqlAlchemyRecommendationRepository(session).add(
        Recommendation(
            id=str(uuid4()),
            profile_id=profile_id,
            kind=RecommendationKind.CONVERSATION_ADVICE,
            source=RecommendationSource.CONVERSATION,
            status=RecommendationStatus.PENDING,
            generated_at=datetime(2026, 8, 1),
            payload={"topic": topic, "title": "Comprometimento da renda"},
            input_fingerprint="fp",
        )
    )
    return recommendation.id


def _raise(topic: str, refs: Optional[list[str]] = None, block_id: str = "t") -> FakeBlock:
    return FakeBlock(
        type="tool_use",
        name="raise_opportunity",
        id=block_id,
        input={
            "topic": topic,
            "title": f"Título de {topic}",
            "diagnosis": f"Diagnóstico de {topic}.",
            "suggested_actions": [f"Ação para {topic}"],
            "evidence_refs": refs or [],
        },
    )


def _read_blocks() -> list[FakeBlock]:
    return [
        FakeBlock(type="tool_use", name="get_dashboard_summary", input={}, id="r1"),
        FakeBlock(type="tool_use", name="list_fragilities", input={}, id="r2"),
    ]


def test_uma_resposta_com_quatro_oportunidades_vira_quatro_blocos(session: Session) -> None:
    profile = _make_profile(session)
    _with_income_and_obligation(session, profile.id)
    _add_finding(session, profile.id, "RESERVE_BELOW_THREE_MONTHS", Severity.HIGH)
    plan_id = _add_active_plan(session, profile.id, "GOAL_ACCELERATION_OPPORTUNITY")

    llm = FakeLLM(
        [
            FakeResponse(content=_read_blocks()),
            FakeResponse(
                content=[
                    _raise("income_commitment", ["ev1"], "o1"),
                    _raise("emergency_reserve", ["ev2"], "o2"),
                    _raise("annual_expense_provision", ["ev2"], "o3"),
                    _raise("goal_acceleration", [], "o4"),
                ]
            ),
            FakeResponse(content=[FakeBlock(type="text", text="Encontrei alguns pontos para conversarmos.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="O que devo olhar?"
    )

    assert [item.topic for item in reply.opportunities] == [
        "income_commitment",
        "emergency_reserve",
        "annual_expense_provision",
        "goal_acceleration",
    ]
    # Identidade própria dentro da mensagem.
    assert len({item.id for item in reply.opportunities}) == 4
    assert all(item.id.startswith(reply.message_id) for item in reply.opportunities)

    commitment, reserve, provision, goal = reply.opportunities

    # Evidências próprias: cada bloco aponta a leitura que o sustenta.
    assert commitment.evidence_references == ("ev1",)
    assert reserve.evidence_references == ("ev2",)
    assert goal.evidence_references == ()

    # Ações próprias: quem tem motor pode simular; quem já tem plano ativo não
    # oferece salvar de novo.
    assert commitment.available_actions == ("save",)
    assert reserve.available_actions == ("simulate", "save")
    assert provision.available_actions == ("simulate", "save")
    assert goal.available_actions == ("view_plan",)
    assert goal.related_plan_id == plan_id

    # Nenhuma classificação inventada: só existe assessment onde o domínio
    # produziu um.
    assert commitment.assessment.tier == "attention"
    assert commitment.assessment.value == Decimal("0.60")
    assert commitment.assessment.policy_id == "income_commitment_bands"
    assert reserve.assessment.severity == "high"
    assert reserve.assessment.policy_id == "RESERVE_BELOW_THREE_MONTHS"
    assert provision.assessment is None
    assert goal.assessment is None

    # O texto conversacional é preservado e não carrega os blocos.
    assert reply.reply == "Encontrei alguns pontos para conversarmos."


def test_assunto_com_recomendacao_equivalente_oferece_ver_recomendacao(session: Session) -> None:
    profile = _make_profile(session)
    _with_income_and_obligation(session, profile.id)
    recommendation_id = _add_pending_conversation_recommendation(session, profile.id, "income_commitment")

    llm = FakeLLM(
        [
            FakeResponse(content=[_raise("income_commitment")]),
            FakeResponse(content=[FakeBlock(type="text", text="Já registramos isso.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="E o comprometimento?"
    )

    opportunity = reply.opportunities[0]
    assert opportunity.available_actions == ("view_recommendation",)
    assert opportunity.related_recommendation_id == recommendation_id


def test_assunto_nao_simulavel_nao_oferece_simular(session: Session) -> None:
    profile = _make_profile(session)

    llm = FakeLLM(
        [
            FakeResponse(content=[_raise("debt_service")]),
            FakeResponse(content=[FakeBlock(type="text", text="Vale olhar suas dívidas.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="E minhas dívidas?"
    )

    opportunity = reply.opportunities[0]
    assert "simulate" not in opportunity.available_actions
    assert opportunity.requires_simulation is False
    assert opportunity.simulation_status.value == "not_required"


def test_assunto_simulavel_nasce_nao_simulado(session: Session) -> None:
    profile = _make_profile(session)

    llm = FakeLLM(
        [
            FakeResponse(content=[_raise("emergency_reserve")]),
            FakeResponse(content=[FakeBlock(type="text", text="Sua reserva merece atenção.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="E a reserva?"
    )

    opportunity = reply.opportunities[0]
    assert opportunity.requires_simulation is True
    assert opportunity.simulation_status.value == "not_simulated"
    assert "simulate" in opportunity.available_actions


def test_assunto_fora_do_catalogo_nao_vira_bloco(session: Session) -> None:
    profile = _make_profile(session)

    llm = FakeLLM(
        [
            FakeResponse(content=[_raise("comprar_bitcoin")]),
            FakeResponse(content=[FakeBlock(type="text", text="Isso está fora do que eu acompanho.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="E cripto?"
    )

    assert reply.opportunities == []


def test_referencia_a_evidencia_inexistente_e_descartada(session: Session) -> None:
    profile = _make_profile(session)

    llm = FakeLLM(
        [
            FakeResponse(content=[_raise("emergency_reserve", ["ev9"])]),
            FakeResponse(content=[FakeBlock(type="text", text="Vamos falar da reserva.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="E a reserva?"
    )

    assert reply.opportunities[0].evidence_references == ()


def test_o_mesmo_assunto_nao_vira_dois_blocos(session: Session) -> None:
    profile = _make_profile(session)

    llm = FakeLLM(
        [
            FakeResponse(content=[_raise("emergency_reserve", block_id="o1"), _raise("emergency_reserve", block_id="o2")]),
            FakeResponse(content=[FakeBlock(type="text", text="Sobre a reserva.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="E a reserva?"
    )

    assert len(reply.opportunities) == 1


def test_blocos_sao_persistidos_e_devolvidos_no_historico(session: Session) -> None:
    profile = _make_profile(session)
    _with_income_and_obligation(session, profile.id)

    llm = FakeLLM(
        [
            FakeResponse(content=[FakeBlock(type="tool_use", name="get_dashboard_summary", input={}, id="r1")]),
            FakeResponse(content=[_raise("income_commitment", ["ev1"])]),
            FakeResponse(content=[FakeBlock(type="text", text="Segue o panorama.")]),
        ]
    )

    reply = _make_use_case(session, llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="Panorama?"
    )

    stored = SqlAlchemyAgentMessageRepository(session).get(reply.message_id)
    history = AgentMessageHistoryItem.from_domain(stored)

    assert [item.topic for item in history.opportunities] == ["income_commitment"]
    assert history.opportunities[0].assessment.tier == "attention"
    assert history.opportunities[0].available_actions == ["save"]


def test_mensagem_antiga_sem_oportunidades_continua_valida(session: Session) -> None:
    """Nada é migrado nem reescrito: ausência de blocos é resposta sem blocos."""
    profile = _make_profile(session)
    conversation_repo = SqlAlchemyConversationRepository(session)
    conversation = Conversation(
        id=str(uuid4()),
        profile_id=profile.id,
        created_at=datetime(2026, 7, 1),
        updated_at=datetime(2026, 7, 1),
    )
    conversation_repo.add(conversation)

    message_repo = SqlAlchemyAgentMessageRepository(session)
    message_repo.add(
        AgentMessage(
            id=str(uuid4()),
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Resposta gravada antes dos blocos estruturados.",
            created_at=datetime(2026, 7, 1),
        )
    )

    stored = message_repo.list_by_conversation(conversation.id)[0]
    history = AgentMessageHistoryItem.from_domain(stored)

    assert stored.opportunities == []
    assert history.opportunities == []
    assert history.content == "Resposta gravada antes dos blocos estruturados."
