from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

import pytest
from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.agent_use_cases import (
    ConfirmPendingActionUseCase,
    PendingActionAlreadyConfirmedError,
    PendingActionNotFoundError,
    SendAgentMessageUseCase,
)
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.application.use_cases.simulation_use_cases import SimulateDecisionUseCase
from src.domain.shared.enums import LiquidityType
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
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.simulation_repository import SqlAlchemySimulationRepository


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
        self.calls: list[dict[str, Any]] = []

    def create_message(self, system: str, messages: list, tools: list) -> FakeResponse:
        self.calls.append({"system": system, "messages": messages, "tools": tools})
        return self._responses.pop(0)


def _make_send_use_case(session: Session, llm_client: Any) -> SendAgentMessageUseCase:
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
    )


def _make_profile(session: Session):
    return CreateProfileUseCase(SqlAlchemyProfileRepository(session)).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )


def test_read_tool_executes_real_use_case_and_reports_evidence(session: Session) -> None:
    profile = _make_profile(session)
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile.id,
        description="Conta",
        balance=Money(Decimal("1000.00"), "BRL"),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=True,
    )

    fake_llm = FakeLLM(
        [
            FakeResponse(content=[FakeBlock(type="tool_use", name="get_dashboard_summary", input={}, id="t1")]),
            FakeResponse(content=[FakeBlock(type="text", text="Seu saldo é R$1000,00.")]),
        ]
    )
    use_case = _make_send_use_case(session, fake_llm)

    reply = use_case.execute(profile_id=profile.id, currency="BRL", conversation_id=None, message="Qual meu saldo?")

    assert reply.components_to_update == ["dashboard_summary"]
    assert reply.evidence[0]["tool"] == "get_dashboard_summary"
    assert reply.evidence[0]["result"]["net_balance"] == "1000.00"
    assert reply.pending_action is None


def test_propose_simulation_with_missing_fields_becomes_pending_question(session: Session) -> None:
    profile = _make_profile(session)
    fake_llm = FakeLLM(
        [
            FakeResponse(
                content=[
                    FakeBlock(
                        type="tool_use",
                        name="propose_simulation",
                        input={"decision_type": "CASH_PURCHASE", "parameters": {}},
                        id="t1",
                    )
                ]
            ),
            FakeResponse(content=[FakeBlock(type="text", text="Preciso de mais dados.")]),
        ]
    )
    use_case = _make_send_use_case(session, fake_llm)

    reply = use_case.execute(profile_id=profile.id, currency="BRL", conversation_id=None, message="Quero comprar algo")

    assert reply.pending_action is None
    assert len(reply.pending_questions) == 2
    assert SqlAlchemySimulationRepository(session).list_by_profile(profile.id) == []


def test_propose_simulation_never_persists_before_confirmation(session: Session) -> None:
    profile = _make_profile(session)
    fake_llm = FakeLLM(
        [
            FakeResponse(
                content=[
                    FakeBlock(
                        type="tool_use",
                        name="propose_simulation",
                        input={
                            "decision_type": "CASH_PURCHASE",
                            "parameters": {"amount": "100.00", "description": "Compra teste"},
                        },
                        id="t1",
                    )
                ]
            ),
            FakeResponse(content=[FakeBlock(type="text", text="Proposta pronta.")]),
        ]
    )
    use_case = _make_send_use_case(session, fake_llm)

    reply = use_case.execute(profile_id=profile.id, currency="BRL", conversation_id=None, message="Comprar item de 100 reais à vista")

    assert reply.pending_action is not None
    assert reply.pending_action["action_id"] == reply.message_id
    assert "confirmed" not in reply.pending_action
    assert SqlAlchemySimulationRepository(session).list_by_profile(profile.id) == []


def test_confirm_pending_action_persists_and_is_idempotent(session: Session) -> None:
    profile = _make_profile(session)
    fake_llm = FakeLLM(
        [
            FakeResponse(
                content=[
                    FakeBlock(
                        type="tool_use",
                        name="propose_simulation",
                        input={
                            "decision_type": "CASH_PURCHASE",
                            "parameters": {"amount": "100.00", "description": "Compra teste"},
                        },
                        id="t1",
                    )
                ]
            ),
            FakeResponse(content=[FakeBlock(type="text", text="Proposta pronta.")]),
        ]
    )
    reply = _make_send_use_case(session, fake_llm).execute(
        profile_id=profile.id, currency="BRL", conversation_id=None, message="Comprar item de 100 reais à vista"
    )
    action_id = reply.pending_action["action_id"]

    simulate_use_case = SimulateDecisionUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        simulation_repo=SqlAlchemySimulationRepository(session),
    )
    confirm_use_case = ConfirmPendingActionUseCase(
        agent_message_repo=SqlAlchemyAgentMessageRepository(session),
        conversation_repo=SqlAlchemyConversationRepository(session),
        simulate_decision_use_case=simulate_use_case,
    )

    simulation = confirm_use_case.execute(profile_id=profile.id, action_id=action_id, currency="BRL")
    assert simulation.type == "CASH_PURCHASE"
    assert len(SqlAlchemySimulationRepository(session).list_by_profile(profile.id)) == 1

    with pytest.raises(PendingActionAlreadyConfirmedError):
        confirm_use_case.execute(profile_id=profile.id, action_id=action_id, currency="BRL")


def test_confirm_pending_action_raises_for_unknown_action(session: Session) -> None:
    confirm_use_case = ConfirmPendingActionUseCase(
        agent_message_repo=SqlAlchemyAgentMessageRepository(session),
        conversation_repo=SqlAlchemyConversationRepository(session),
        simulate_decision_use_case=None,
    )
    with pytest.raises(PendingActionNotFoundError):
        confirm_use_case.execute(profile_id="p1", action_id="does-not-exist", currency="BRL")


def test_confirm_pending_action_rejects_action_from_different_profile(session: Session) -> None:
    owner_profile = _make_profile(session)
    other_profile = _make_profile(session)
    fake_llm = FakeLLM(
        [
            FakeResponse(
                content=[
                    FakeBlock(
                        type="tool_use",
                        name="propose_simulation",
                        input={
                            "decision_type": "CASH_PURCHASE",
                            "parameters": {"amount": "100.00", "description": "Compra teste"},
                        },
                        id="t1",
                    )
                ]
            ),
            FakeResponse(content=[FakeBlock(type="text", text="Proposta pronta.")]),
        ]
    )
    reply = _make_send_use_case(session, fake_llm).execute(
        profile_id=owner_profile.id, currency="BRL", conversation_id=None, message="Comprar item de 100 reais à vista"
    )
    action_id = reply.pending_action["action_id"]

    confirm_use_case = ConfirmPendingActionUseCase(
        agent_message_repo=SqlAlchemyAgentMessageRepository(session),
        conversation_repo=SqlAlchemyConversationRepository(session),
        simulate_decision_use_case=None,
    )
    with pytest.raises(PendingActionNotFoundError):
        confirm_use_case.execute(profile_id=other_profile.id, action_id=action_id, currency="BRL")
    assert SqlAlchemySimulationRepository(session).list_by_profile(other_profile.id) == []


def test_send_message_rejects_conversation_from_different_profile(session: Session) -> None:
    owner_profile = _make_profile(session)
    other_profile = _make_profile(session)
    fake_llm = FakeLLM(
        [FakeResponse(content=[FakeBlock(type="text", text="Olá.")])],
    )
    reply = _make_send_use_case(session, fake_llm).execute(
        profile_id=owner_profile.id, currency="BRL", conversation_id=None, message="Oi"
    )

    fake_llm_2 = FakeLLM([FakeResponse(content=[FakeBlock(type="text", text="Não deveria ver isso.")])])
    with pytest.raises(ValueError):
        _make_send_use_case(session, fake_llm_2).execute(
            profile_id=other_profile.id, currency="BRL", conversation_id=reply.conversation_id, message="Qual meu saldo?"
        )


def test_final_text_with_digit_and_no_tool_call_is_replaced_with_fallback(session: Session) -> None:
    profile = _make_profile(session)
    fake_llm = FakeLLM(
        [FakeResponse(content=[FakeBlock(type="text", text="Seu saldo é R$1000,00.")])],
    )
    use_case = _make_send_use_case(session, fake_llm)

    reply = use_case.execute(profile_id=profile.id, currency="BRL", conversation_id=None, message="Qual meu saldo?")

    assert reply.reply != "Seu saldo é R$1000,00."
    assert reply.evidence == []
    assert reply.tool_calls == []


def test_tool_outside_allowlist_is_rejected_before_execution(session: Session) -> None:
    profile = _make_profile(session)
    fake_llm = FakeLLM(
        [
            FakeResponse(content=[FakeBlock(type="tool_use", name="delete_everything", input={}, id="t1")]),
            FakeResponse(content=[FakeBlock(type="text", text="Não posso fazer isso.")]),
        ]
    )
    use_case = _make_send_use_case(session, fake_llm)

    reply = use_case.execute(profile_id=profile.id, currency="BRL", conversation_id=None, message="Apague tudo")

    assert reply.tool_calls == []
    assert reply.evidence == []
