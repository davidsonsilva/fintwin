"""Casos de uso do agente conversacional (Spec seções 6.8, 7, 18.11 e 25).

Fluxo obrigatório (seção 7): mensagem do usuário -> interpretador de intenção
(Claude + tool calling) -> schema validado -> caso de uso -> motor
determinístico -> resultado estruturado -> agente explica.

Nenhuma tool fora da allowlist (`_ALLOWED_TOOLS`) é executada (seção 25). A
tool `propose_simulation` NUNCA persiste — apenas valida e empacota os
parâmetros; a persistência real só acontece em `ConfirmPendingActionUseCase`,
que não volta a chamar o LLM (garante o critério de aceite #18 do MVP: "o
agente não calcula valores por conta própria" também no caminho de escrita).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional
from uuid import uuid4

from src.application.use_cases.autonomy_use_cases import GetAutonomyUseCase
from src.application.use_cases.dashboard_use_cases import GetDashboardSummaryUseCase
from src.application.use_cases.fragility_use_cases import ListFragilitiesUseCase
from src.domain.agent.entities import AgentMessage, Conversation
from src.domain.decisions.entities import Simulation
from src.domain.decisions.types import DECISION_TYPES
from src.domain.decisions.validation import InvalidDecisionParametersError, validate_decision_parameters
from src.domain.shared.enums import MessageRole, Severity

_MANDATORY_LIMITATION = (
    "O FinTwin AI MVP é uma ferramenta educacional e de simulação. Ele não oferece "
    "consultoria financeira, recomendação de investimento ou garantia sobre resultados futuros."
)

_NO_EVIDENCE_FALLBACK = (
    "Não tenho essa informação sem consultar uma ferramenta. Pergunte novamente para que "
    "eu busque o dado correto antes de responder com números."
)

_LOOKS_LIKE_MONEY = re.compile(r"r\$\s?\d|\breais\b|\d+[.,]\d{2}\b", re.IGNORECASE)

_SYSTEM_PROMPT = """Você é o agente conversacional do FinTwin AI, uma plataforma de simulação e prevenção financeira.

Regras invioláveis:
- Você NUNCA calcula ou declara um valor financeiro por conta própria. Todo número que você mencionar na resposta deve vir do resultado de uma tool chamada nesta mesma conversa.
- Se faltar um dado necessário para propor uma simulação, pergunte objetivamente qual dado falta, em vez de assumir um valor.
- A tool propose_simulation NÃO persiste nada — apenas valida os parâmetros. A simulação só é executada e salva depois que o usuário confirmar explicitamente na interface.
- Não invente fragilidades, indicadores ou simulações que não vieram de uma tool.
- Você não substitui o dashboard: seu papel é explicar resultados, não ser a única forma de interação.
"""

_MAX_TOOL_ITERATIONS = 3

_COMPONENT_BY_TOOL = {
    "get_dashboard_summary": "dashboard_summary",
    "get_autonomy": "autonomy",
    "list_fragilities": "fragilities",
}

_ALLOWED_TOOLS = frozenset({"get_dashboard_summary", "get_autonomy", "list_fragilities", "propose_simulation"})


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "get_dashboard_summary",
            "description": (
                "Obtém o resumo atual do dashboard do perfil: saldo líquido, obrigações mensais, "
                "comprometimento de renda, meta principal e próximos eventos."
            ),
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_autonomy",
            "description": (
                "Obtém o Índice de Autonomia Financeira atual do perfil (meses de autonomia nos "
                "cenários provável, adverso e de perda de renda)."
            ),
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "list_fragilities",
            "description": "Lista as fragilidades financeiras já detectadas para o perfil (não executa uma nova detecção).",
            "input_schema": {
                "type": "object",
                "properties": {"severity": {"type": "string", "enum": [s.value for s in Severity]}},
                "required": [],
            },
        },
        {
            "name": "propose_simulation",
            "description": (
                "Valida e propõe os parâmetros de uma simulação de decisão financeira. NÃO persiste "
                "nada — apenas valida o schema e retorna uma proposta que o usuário deve confirmar "
                "explicitamente na interface antes de ser executada."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "decision_type": {"type": "string", "enum": list(DECISION_TYPES.keys())},
                    "parameters": {"type": "object"},
                },
                "required": ["decision_type", "parameters"],
            },
        },
    ]


@dataclass
class AgentReply:
    conversation_id: str
    message_id: str
    reply: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    pending_action: Optional[dict[str, Any]] = None
    components_to_update: list[str] = field(default_factory=list)
    pending_questions: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=lambda: [_MANDATORY_LIMITATION])


class PendingActionNotFoundError(ValueError):
    pass


class PendingActionAlreadyConfirmedError(ValueError):
    pass


class SendAgentMessageUseCase:
    def __init__(
        self,
        llm_client: Any,
        conversation_repo: Any,
        agent_message_repo: Any,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
        fragility_repo: Any,
    ) -> None:
        self._llm = llm_client
        self._conversation_repo = conversation_repo
        self._agent_message_repo = agent_message_repo
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._debt_repo = debt_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo
        self._fragility_repo = fragility_repo

    def _execute_read_tool(self, tool_name: str, tool_input: Mapping[str, Any], profile_id: str, currency: str) -> dict[str, Any]:
        if tool_name == "get_dashboard_summary":
            summary = GetDashboardSummaryUseCase(
                self._account_repo, self._income_repo, self._obligation_repo, self._goal_repo, self._event_repo
            ).execute(profile_id, currency)
            return {
                "net_balance": str(summary.net_balance.amount),
                "currency": summary.currency,
                "monthly_obligations_total": str(summary.monthly_obligations_total.amount),
                "income_commitment_pct": (
                    str(summary.income_commitment_pct.as_fraction()) if summary.income_commitment_pct else None
                ),
                "main_goal": summary.main_goal.description if summary.main_goal else None,
                "upcoming_events_count": len(summary.upcoming_events),
            }
        if tool_name == "get_autonomy":
            result = GetAutonomyUseCase(
                self._account_repo,
                self._income_repo,
                self._obligation_repo,
                self._debt_repo,
                self._goal_repo,
                self._event_repo,
            ).execute(profile_id, currency, expense_reduction_capacity=None)
            return {
                "basic_autonomy_months": (
                    str(result.basic_autonomy_months) if result.basic_autonomy_months is not None else None
                ),
                "probable_autonomy_months": (
                    str(result.probable_autonomy_months) if result.probable_autonomy_months is not None else None
                ),
                "adverse_autonomy_months": (
                    str(result.adverse_autonomy_months) if result.adverse_autonomy_months is not None else None
                ),
                "income_loss_autonomy_months": (
                    str(result.income_loss_autonomy_months) if result.income_loss_autonomy_months is not None else None
                ),
            }
        if tool_name == "list_fragilities":
            severity = tool_input.get("severity")
            findings = ListFragilitiesUseCase(self._fragility_repo).execute(
                profile_id, severity=Severity(severity) if severity else None
            )
            return {"findings": [{"code": f.code, "severity": f.severity.value, "evidence": f.evidence} for f in findings]}
        raise ValueError(f"Tool de leitura desconhecida: {tool_name!r}")

    def _propose_simulation(self, tool_input: Mapping[str, Any]) -> dict[str, Any]:
        decision_type = tool_input.get("decision_type")
        parameters = dict(tool_input.get("parameters") or {})
        if decision_type not in DECISION_TYPES:
            return {"status": "error", "error": f"Tipo de decisão desconhecido: {decision_type!r}"}

        required = DECISION_TYPES[decision_type].required_parameters
        missing = [field_name for field_name in required if parameters.get(field_name) in (None, "")]
        if missing:
            return {"status": "missing_fields", "decision_type": decision_type, "missing_fields": missing}

        try:
            validate_decision_parameters(decision_type, parameters)
        except InvalidDecisionParametersError as exc:
            return {"status": "invalid", "error": str(exc)}

        return {"status": "ready", "decision_type": decision_type, "parameters": parameters}

    def execute(
        self,
        profile_id: str,
        currency: str,
        conversation_id: Optional[str],
        message: str,
    ) -> AgentReply:
        now = datetime.utcnow()
        if conversation_id is not None:
            conversation = self._conversation_repo.get(conversation_id)
            if conversation is None or conversation.profile_id != profile_id:
                raise ValueError(f"Conversa não encontrada: {conversation_id!r}")
        else:
            conversation = Conversation(id=str(uuid4()), profile_id=profile_id, created_at=now, updated_at=now)
            self._conversation_repo.add(conversation)

        history = self._agent_message_repo.list_by_conversation(conversation.id)
        conversation_messages: list[dict[str, Any]] = [
            {"role": entry.role.value, "content": entry.content} for entry in history if entry.content
        ]
        conversation_messages.append({"role": "user", "content": message})

        tool_calls: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        pending_action: Optional[dict[str, Any]] = None
        pending_questions: list[str] = []
        components_to_update: list[str] = []
        final_text = ""
        message_id = str(uuid4())

        for _ in range(_MAX_TOOL_ITERATIONS):
            response = self._llm.create_message(
                system=_SYSTEM_PROMPT, messages=conversation_messages, tools=_tool_definitions()
            )
            text_blocks = [block.text for block in response.content if block.type == "text"]
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            final_text = "\n".join(text_blocks).strip()

            if not tool_use_blocks:
                break

            conversation_messages.append({"role": "assistant", "content": response.content})
            tool_results: list[dict[str, Any]] = []
            for block in tool_use_blocks:
                if block.name not in _ALLOWED_TOOLS:
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": "Tool não permitida.", "is_error": True}
                    )
                    continue

                tool_calls.append({"tool": block.name, "input": block.input})

                if block.name == "propose_simulation":
                    result = self._propose_simulation(block.input)
                    if result["status"] == "ready":
                        pending_action = {
                            "action_id": message_id,
                            "decision_type": result["decision_type"],
                            "parameters": result["parameters"],
                        }
                    elif result["status"] == "missing_fields":
                        pending_questions.extend(
                            f"Preciso do campo '{field_name}' para simular {result['decision_type']}."
                            for field_name in result["missing_fields"]
                        )
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result, ensure_ascii=False)}
                    )
                else:
                    result = self._execute_read_tool(block.name, block.input, profile_id, currency)
                    component = _COMPONENT_BY_TOOL.get(block.name)
                    if component and component not in components_to_update:
                        components_to_update.append(component)
                    evidence.append({"tool": block.name, "result": result})
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result, ensure_ascii=False)}
                    )
            conversation_messages.append({"role": "user", "content": tool_results})

        if final_text and _LOOKS_LIKE_MONEY.search(final_text) and not evidence:
            final_text = _NO_EVIDENCE_FALLBACK

        conversation.updated_at = datetime.utcnow()
        self._conversation_repo.update(conversation)

        self._agent_message_repo.add(
            AgentMessage(id=str(uuid4()), conversation_id=conversation.id, role=MessageRole.USER, content=message, created_at=now)
        )
        self._agent_message_repo.add(
            AgentMessage(
                id=message_id,
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=final_text,
                tool_calls=tool_calls,
                pending_action=pending_action,
                created_at=datetime.utcnow(),
            )
        )

        return AgentReply(
            conversation_id=conversation.id,
            message_id=message_id,
            reply=final_text,
            tool_calls=tool_calls,
            pending_action=pending_action,
            components_to_update=components_to_update,
            pending_questions=pending_questions,
            evidence=evidence,
        )


class ConfirmPendingActionUseCase:
    def __init__(self, agent_message_repo: Any, conversation_repo: Any, simulate_decision_use_case: Any) -> None:
        self._agent_message_repo = agent_message_repo
        self._conversation_repo = conversation_repo
        self._simulate_decision_use_case = simulate_decision_use_case

    def execute(self, profile_id: str, action_id: str, currency: str, horizon_months: int = 12) -> Simulation:
        agent_message = self._agent_message_repo.get(action_id)
        if agent_message is None or agent_message.pending_action is None:
            raise PendingActionNotFoundError(f"Ação pendente não encontrada: {action_id!r}")

        conversation = self._conversation_repo.get(agent_message.conversation_id)
        if conversation is None or conversation.profile_id != profile_id:
            raise PendingActionNotFoundError(f"Ação pendente não encontrada: {action_id!r}")

        # Claim atômico (UPDATE condicional no banco) - se duas confirmações chegarem
        # ao mesmo tempo, só uma consegue marcar confirmed=True; a outra recebe False
        # aqui e nunca chega a chamar o motor de simulação (evita duplicar a persistência).
        claimed = self._agent_message_repo.try_claim(action_id)
        if not claimed:
            raise PendingActionAlreadyConfirmedError(f"Ação pendente já confirmada: {action_id!r}")

        pending = agent_message.pending_action
        decision_type = pending["decision_type"]
        parameters = pending["parameters"]
        validate_decision_parameters(decision_type, parameters)

        return self._simulate_decision_use_case.execute(
            profile_id=profile_id,
            decision_type=decision_type,
            parameters=parameters,
            scenario_override=None,
            horizon_months=horizon_months,
            currency=currency,
        )
