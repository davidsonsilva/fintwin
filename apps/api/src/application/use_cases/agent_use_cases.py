# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

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
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence
from uuid import uuid4

from src.application.use_cases.autonomy_use_cases import GetAutonomyUseCase
from src.application.use_cases.dashboard_use_cases import GetDashboardSummaryUseCase
from src.application.use_cases.fragility_use_cases import ListFragilitiesUseCase
from src.domain.agent import opportunities as opportunity_blocks
from src.domain.agent.entities import AgentMessage, Conversation
from src.domain.agent.opportunities import ActionableOpportunity, OpportunityAssessment
from src.domain.agent.topics import AGENT_TOPICS, TOPIC_CODES, AgentTopic, AssessmentSource
from src.domain.decisions.entities import Simulation
from src.domain.decisions.types import DECISION_TYPES
from src.domain.decisions.validation import InvalidDecisionParametersError, validate_decision_parameters
from src.domain.fragility.rules import RULES_VERSION
from src.domain.preventive_plans.entities import ACTIVE_PLAN_STATUSES
from src.domain.recommendations.entities import RecommendationKind
from src.domain.shared.enums import MessageRole, Severity
from src.domain.shared.indicators import (
    INCOME_COMMITMENT_POLICY_ID,
    INCOME_COMMITMENT_POLICY_VERSION,
    classify_income_commitment,
)

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
- Você NUNCA classifica um indicador como saudável, aceitável, elevado ou crítico por conta própria, e NUNCA cita um limiar ("acima de 50%", "o ideal é até 30%") que não tenha vindo de uma tool. Os limiares do FinTwin são definidos no domínio: use exatamente o campo de classificação devolvido pela tool (por exemplo `income_commitment_status.label`). Se a tool não trouxer classificação para um indicador, apresente o número sem julgá-lo.
- Se faltar um dado necessário para propor uma simulação, pergunte objetivamente qual dado falta, em vez de assumir um valor.
- A tool propose_simulation NÃO persiste nada — apenas valida os parâmetros. A simulação só é executada e salva depois que o usuário confirmar explicitamente na interface.
- Não invente fragilidades, indicadores ou simulações que não vieram de uma tool.
- Você não substitui o dashboard: seu papel é explicar resultados, não ser a única forma de interação.

Oportunidades acionáveis:
- Sempre que sua resposta identificar uma oportunidade financeira acionável, declare-a com a tool raise_opportunity — uma chamada por oportunidade. Se a resposta tem quatro oportunidades, são quatro chamadas.
- O texto da resposta é apenas a explicação em linguagem natural. Não escreva seções como "O que fazer", não numere oportunidades e não repita o conteúdo dos blocos em formato de lista estruturada: a interface monta os blocos a partir das chamadas da tool, não do seu texto.
- Em raise_opportunity você NÃO informa valores, percentuais, classificações, severidades, limiares nem prioridade de risco. O backend anexa a classificação oficial quando ela existe; quando não existe, a oportunidade sai sem classificação — e você também não a inventa no texto.
- Cite em evidence_refs os identificadores `evidence_id` devolvidos pelas tools de leitura que sustentam aquela oportunidade específica.
- Só existe oportunidade para os assuntos do catálogo (campo topic). Assunto fora do catálogo é explicado no texto e não vira bloco.
"""

_MAX_TOOL_ITERATIONS = 3

_COMPONENT_BY_TOOL = {
    "get_dashboard_summary": "dashboard_summary",
    "get_autonomy": "autonomy",
    "list_fragilities": "fragilities",
}

_ALLOWED_TOOLS = frozenset(
    {"get_dashboard_summary", "get_autonomy", "list_fragilities", "propose_simulation", "raise_opportunity"}
)

#: Tools cujo resultado conta como evidência de leitura. `propose_simulation` e
#: `raise_opportunity` não leem nada do perfil — tratá-las como evidência
#: reabriria a brecha do guard anti-valor-inventado (achado da VS-09).
_READ_TOOLS = frozenset({"get_dashboard_summary", "get_autonomy", "list_fragilities"})


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
        {
            "name": "raise_opportunity",
            "description": (
                "Declara UMA oportunidade financeira acionável identificada nesta resposta. Chame "
                "uma vez por oportunidade. Não informe valores, percentuais, classificações, "
                "severidades nem limiares: o backend anexa a classificação oficial do assunto "
                "quando ela existe. Não persiste nada — apenas estrutura o bloco que a interface "
                "vai exibir."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "enum": list(TOPIC_CODES)},
                    "title": {"type": "string", "description": "Título curto da oportunidade, em português."},
                    "diagnosis": {
                        "type": "string",
                        "description": "O que foi observado, em uma ou duas frases, sem números inventados.",
                    },
                    "suggested_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "O que a pessoa pode fazer, uma ação por item.",
                    },
                    "evidence_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Identificadores `evidence_id` das tools de leitura que sustentam esta oportunidade.",
                    },
                },
                "required": ["topic", "title", "diagnosis", "suggested_actions"],
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
    #: Blocos estruturados da resposta. Uma resposta pode conter vários.
    opportunities: list[ActionableOpportunity] = field(default_factory=list)
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
        recommendation_repo: Any,
        plan_repo: Any,
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
        self._recommendation_repo = recommendation_repo
        self._plan_repo = plan_repo

    def _execute_read_tool(self, tool_name: str, tool_input: Mapping[str, Any], profile_id: str, currency: str) -> dict[str, Any]:
        if tool_name == "get_dashboard_summary":
            summary = GetDashboardSummaryUseCase(
                self._account_repo, self._income_repo, self._obligation_repo, self._goal_repo, self._event_repo
            ).execute(profile_id, currency)
            commitment = summary.income_commitment_pct
            # O número sozinho não diz nada, e o prompt proíbe o agente de
            # classificá-lo. A classificação vem junto, da mesma régua que o
            # gauge do dashboard usa.
            assessment = classify_income_commitment(commitment.as_fraction()) if commitment else None
            return {
                "net_balance": str(summary.net_balance.amount),
                "currency": summary.currency,
                "monthly_obligations_total": str(summary.monthly_obligations_total.amount),
                "income_commitment_pct": str(commitment.as_fraction()) if commitment else None,
                "income_commitment_status": (
                    {"tier": assessment.tier.value, "label": assessment.label} if assessment is not None else None
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

    def _assessment_for(
        self, topic: AgentTopic, evidence: Sequence[Mapping[str, Any]]
    ) -> Optional[OpportunityAssessment]:
        """A classificação oficial do assunto, se alguma tool de leitura a produziu.

        Não há caminho para uma classificação fabricada: ou ela veio do domínio
        nesta mesma mensagem, ou a oportunidade sai sem `assessment`.
        """
        if topic.assessment is AssessmentSource.INCOME_COMMITMENT:
            for item in evidence:
                if item["tool"] != "get_dashboard_summary":
                    continue
                status = item["result"].get("income_commitment_status")
                if status is None:
                    continue
                raw_pct = item["result"].get("income_commitment_pct")
                return OpportunityAssessment(
                    value=Decimal(raw_pct) if raw_pct is not None else None,
                    tier=status["tier"],
                    policy_id=INCOME_COMMITMENT_POLICY_ID,
                    policy_version=INCOME_COMMITMENT_POLICY_VERSION,
                )
        if topic.assessment is AssessmentSource.FRAGILITY_FINDING:
            for item in evidence:
                if item["tool"] != "list_fragilities":
                    continue
                for finding in item["result"]["findings"]:
                    if finding["code"] in topic.fragility_codes:
                        return OpportunityAssessment(
                            severity=finding["severity"],
                            policy_id=finding["code"],
                            policy_version=RULES_VERSION,
                        )
        return None

    def _related_plan_id(self, profile_id: str, topic: AgentTopic) -> Optional[str]:
        """Plano ainda em execução que já endereça este assunto."""
        for plan in self._plan_repo.list_by_profile(profile_id):
            if plan.risk_code in topic.plan_risk_codes and plan.status in ACTIVE_PLAN_STATUSES:
                return plan.id
        return None

    def _related_recommendation_id(self, profile_id: str, topic: AgentTopic) -> Optional[str]:
        """Recomendação equivalente aguardando decisão.

        Equivalência é por assunto. O motor identifica o dele pelo `kind`; a
        recomendação nascida da conversa carrega o `topic` no payload, porque
        todas compartilham o mesmo `kind`.
        """
        by_kind = topic.recommendation_kind is not RecommendationKind.CONVERSATION_ADVICE
        for recommendation in self._recommendation_repo.list_pending(profile_id):
            if by_kind and recommendation.kind is topic.recommendation_kind:
                return recommendation.id
            if not by_kind and (recommendation.payload or {}).get("topic") == topic.code:
                return recommendation.id
        return None

    def _raise_opportunity(
        self,
        tool_input: Mapping[str, Any],
        profile_id: str,
        message_id: str,
        evidence: Sequence[Mapping[str, Any]],
        raised: list[ActionableOpportunity],
    ) -> dict[str, Any]:
        topic = AGENT_TOPICS.get(tool_input.get("topic"))
        if topic is None:
            return {"status": "error", "error": f"Assunto fora do catálogo: {tool_input.get('topic')!r}"}
        if any(existing.topic == topic.code for existing in raised):
            # Um assunto é um bloco. Duas chamadas para o mesmo assunto
            # produziriam dois cards competindo pelas mesmas ações.
            return {"status": "already_raised", "topic": topic.code}

        title = (tool_input.get("title") or "").strip() or topic.label
        diagnosis = (tool_input.get("diagnosis") or "").strip()
        if not diagnosis:
            return {"status": "error", "error": "Uma oportunidade precisa de diagnosis."}

        known_evidence = {item["id"] for item in evidence}
        # Referência a evidência inexistente é descartada em silêncio para o
        # usuário, mas devolvida ao modelo: ele precisa saber que o vínculo não
        # colou, e a interface não pode exibir um lastro que não existe.
        refs = [ref for ref in (tool_input.get("evidence_refs") or []) if ref in known_evidence]

        related_plan_id = self._related_plan_id(profile_id, topic)
        opportunity = opportunity_blocks.build_opportunity(
            opportunity_id=f"{message_id}-op{len(raised) + 1}",
            topic=topic,
            title=title,
            diagnosis=diagnosis,
            suggested_actions=[str(action) for action in tool_input.get("suggested_actions") or []],
            evidence_references=refs,
            assessment=self._assessment_for(topic, evidence),
            related_plan_id=related_plan_id,
            related_recommendation_id=(
                None if related_plan_id is not None else self._related_recommendation_id(profile_id, topic)
            ),
        )
        raised.append(opportunity)
        return {"status": "registered", **opportunity_blocks.to_dict(opportunity), "accepted_evidence_refs": refs}

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
        raised: list[ActionableOpportunity] = []
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
                elif block.name == "raise_opportunity":
                    result = self._raise_opportunity(block.input, profile_id, message_id, evidence, raised)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result, ensure_ascii=False)}
                    )
                else:
                    result = self._execute_read_tool(block.name, block.input, profile_id, currency)
                    component = _COMPONENT_BY_TOOL.get(block.name)
                    if component and component not in components_to_update:
                        components_to_update.append(component)
                    # O id acompanha o resultado para o modelo poder apontar,
                    # em `evidence_refs`, qual leitura sustenta cada bloco.
                    evidence_id = f"ev{len(evidence) + 1}"
                    evidence.append({"id": evidence_id, "tool": block.name, "result": result})
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps({"evidence_id": evidence_id, **result}, ensure_ascii=False),
                        }
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
                opportunities=[opportunity_blocks.to_dict(item) for item in raised],
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
            opportunities=raised,
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
