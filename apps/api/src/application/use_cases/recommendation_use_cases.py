# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Ciclo de vida da recomendação proativa.

    insight detectado
    -> recomendação registrada
    -> usuário analisa
    -> aprova ou rejeita
    -> plano preventivo criado quando aprovado
    -> card Insight procura a próxima ação relevante

Detectar é escrita: cria (ou reaproveita) uma recomendação pendente. Ler o
insight é operação pura — o motor roda para produzir o diagnóstico corrente,
mas nada é gravado, porque o card não pode criar registro a cada render.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Mapping, Optional
from uuid import uuid4

from src.application.use_cases.opportunity_links import (
    related_plan_id,
    related_recommendation_id,
)
from src.domain.agent import opportunities as opportunity_blocks
from src.domain.agent.topics import get_topic
from src.domain.opportunity.engine import analyze_opportunity
from src.domain.opportunity.entities import OpportunityResult, OpportunityStatus
from src.domain.opportunity.fingerprint import compute_input_fingerprint
from src.domain.preventive_plans.entities import ACTIVE_PLAN_STATUSES, PreventivePlan
from src.domain.recommendations import lifecycle
from src.domain.recommendations.entities import (
    InsightSurface,
    Recommendation,
    RecommendationKind,
    RecommendationSource,
    RecommendationStatus,
)

ANALYSIS_SCENARIO = "probable"

Serializer = Callable[[OpportunityResult], Mapping[str, Any]]


class _ProfileDataLoader:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
    ) -> None:
        self._repos = {
            "accounts": account_repo,
            "incomes": income_repo,
            "obligations": obligation_repo,
            "debts": debt_repo,
            "goals": goal_repo,
            "events": event_repo,
        }

    def load(self, profile_id: str) -> dict[str, Any]:
        return {key: repo.list_by_profile(profile_id) for key, repo in self._repos.items()}


class _EngineBackedUseCase:
    def __init__(
        self,
        recommendation_repo: Any,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        debt_repo: Any,
        goal_repo: Any,
        event_repo: Any,
        plan_repo: Any = None,
    ) -> None:
        self._repo = recommendation_repo
        self._plan_repo = plan_repo
        self._loader = _ProfileDataLoader(
            account_repo, income_repo, obligation_repo, debt_repo, goal_repo, event_repo
        )

    def _active_plan_id(self, profile_id: str, kind: RecommendationKind) -> Optional[str]:
        """Plano ainda em execução nascido de uma aprovação deste assunto.

        Sem isto o motor recomendaria eternamente a mesma coisa: aprovar não
        movimenta dinheiro, então os dados de entrada não mudam.
        """
        if self._plan_repo is None:
            return None
        for recommendation in self._repo.list_approved(profile_id, kind):
            if recommendation.plan_id is None:
                continue
            plan = self._plan_repo.get(recommendation.plan_id)
            if plan is not None and plan.status in ACTIVE_PLAN_STATUSES:
                return plan.id
        return None

    def _analyze(self, profile_id: str, currency: str, custom_pct: Optional[Decimal] = None):
        data = self._loader.load(profile_id)
        result = analyze_opportunity(currency=currency, custom_pct=custom_pct, **data)
        fingerprint = compute_input_fingerprint(currency=currency, **data)
        return result, fingerprint

    def _fingerprint(self, profile_id: str, currency: str) -> str:
        return compute_input_fingerprint(currency=currency, **self._loader.load(profile_id))


class DetectRecommendationUseCase(_EngineBackedUseCase):
    """Roda o motor e reconcilia o registro com o que ele encontrou."""

    def __init__(self, serializer: Serializer, **repos: Any) -> None:
        super().__init__(**repos)
        self._serialize = serializer

    def execute(
        self, profile_id: str, currency: str, custom_pct: Optional[Decimal] = None
    ) -> InsightSurface:
        kind = RecommendationKind.GOAL_ACCELERATION
        pending = self._repo.get_pending(profile_id, kind)

        # Já existe plano em execução para este assunto: ele não é mais a
        # próxima ação, mesmo que o motor continue enxergando a oportunidade.
        active_plan_id = self._active_plan_id(profile_id, kind)
        if active_plan_id is not None and pending is None:
            result, _ = self._analyze(profile_id, currency)
            return InsightSurface(
                recommendation=None,
                diagnosis=self._serialize(result),
                assumptions=result.assumptions,
                active_plan_id=active_plan_id,
            )

        result, fingerprint = self._analyze(profile_id, currency, custom_pct)

        if result.status is not OpportunityStatus.AVAILABLE:
            # Nada a recomendar agora. Uma pendente anterior perde a validade —
            # mas expira num ato explícito, com registro, nunca em silêncio.
            if pending is not None:
                self._repo.save(lifecycle.expire(pending))
            return InsightSurface(
                recommendation=None,
                diagnosis=self._serialize(result),
                assumptions=result.assumptions,
            )

        # Mesma análise, mesmos dados: reaproveita em vez de encher o registro
        # de cópias idênticas a cada clique.
        if pending is not None and pending.input_fingerprint == fingerprint and custom_pct is None:
            return InsightSurface(recommendation=pending, stale=False)

        created = self._repo.add(
            Recommendation(
                id=str(uuid4()),
                profile_id=profile_id,
                kind=kind,
                source=RecommendationSource.ENGINE,
                status=RecommendationStatus.PENDING,
                generated_at=result.generated_at,
                payload=self._serialize(result),
                input_fingerprint=fingerprint,
                scenario=ANALYSIS_SCENARIO,
                supersedes_id=pending.id if pending else None,
            )
        )
        if pending is not None:
            self._repo.save(lifecycle.supersede(pending, created.id))
        return InsightSurface(recommendation=created, stale=False)


class GetInsightUseCase(_EngineBackedUseCase):
    """O que o card Insight mostra agora. Somente leitura."""

    def __init__(self, serializer: Serializer, **repos: Any) -> None:
        super().__init__(**repos)
        self._serialize = serializer

    def execute(self, profile_id: str, currency: str) -> InsightSurface:
        kind = RecommendationKind.GOAL_ACCELERATION
        pending = self._repo.get_pending(profile_id, kind)
        if pending is not None:
            return InsightSurface(
                recommendation=pending,
                stale=self._fingerprint(profile_id, currency) != pending.input_fingerprint,
            )

        # Sem pendente, o card precisa saber *por que* não há ação: finanças
        # monitoradas e estáveis não é a mesma coisa que dados faltando, nem
        # que um plano já em execução.
        result, _ = self._analyze(profile_id, currency)
        return InsightSurface(
            recommendation=None,
            diagnosis=self._serialize(result),
            assumptions=result.assumptions,
            active_plan_id=self._active_plan_id(profile_id, kind),
        )


class GetRecommendationUseCase(_EngineBackedUseCase):
    """Abre uma recomendação do registro sem recalcular nada."""

    def execute(self, recommendation_id: str, currency: str) -> Optional[InsightSurface]:
        recommendation = self._repo.get(recommendation_id)
        if recommendation is None:
            return None
        stale = (
            recommendation.status is RecommendationStatus.PENDING
            and self._fingerprint(recommendation.profile_id, currency)
            != recommendation.input_fingerprint
        )
        return InsightSurface(recommendation=recommendation, stale=stale)


class DecideRecommendationUseCase(_EngineBackedUseCase):
    """Aprova ou rejeita. Aprovar cria o plano — e move zero dinheiro."""

    def __init__(self, **repos: Any) -> None:
        super().__init__(**repos)

    def execute(
        self,
        recommendation_id: str,
        currency: str,
        approve: bool,
        selected_scenario: Optional[str],
        now: Optional[datetime] = None,
    ) -> Optional[Recommendation]:
        recommendation = self._repo.get(recommendation_id)
        if recommendation is None:
            return None

        now = now or datetime.utcnow()
        lifecycle.ensure_decidable(
            recommendation, self._fingerprint(recommendation.profile_id, currency)
        )

        if not approve:
            return self._repo.save(lifecycle.reject(recommendation, now))

        # Recomendação da conversa não tem cenário calculado, então não vira
        # plano: não há compromisso mensal a acompanhar, só a decisão a
        # registrar. Forçar um plano exigiria inventar números que o motor
        # nunca produziu.
        if recommendation.kind is RecommendationKind.CONVERSATION_ADVICE:
            return self._repo.save(
                lifecycle.approve(recommendation, selected_scenario or "", "", now)
            )

        scenario_key = selected_scenario or (recommendation.payload.get("recommended") or {}).get(
            "key"
        )
        if scenario_key is None:
            raise lifecycle.InvalidTransitionError("Nenhum cenário para aprovar.")

        actions, expected_result = lifecycle.build_plan_payload(
            recommendation.payload, scenario_key
        )
        plan = PreventivePlan(
            id=str(uuid4()),
            profile_id=recommendation.profile_id,
            risk_code=lifecycle.GOAL_ACCELERATION_PLAN_CODE,
            status=lifecycle.initial_plan_status(),
            actions=actions,
            expected_result=expected_result,
            created_at=now,
            approved_at=now,
        )
        self._plan_repo.add(plan)
        return self._repo.save(lifecycle.approve(recommendation, scenario_key, plan.id, now))


class ListRecommendationsUseCase:
    """O registro: pendentes, aprovadas, rejeitadas, expiradas e substituídas."""

    def __init__(self, recommendation_repo: Any) -> None:
        self._repo = recommendation_repo

    def execute(
        self, profile_id: str, status: Optional[RecommendationStatus] = None
    ) -> list[Recommendation]:
        return self._repo.list_by_profile(profile_id, status)


class OpportunityNotFoundError(ValueError):
    """A oportunidade citada não existe na mensagem indicada."""


class OpportunityActionOutdatedError(Exception):
    """A ação exibida não vale mais; o estado atual é outro.

    Não é erro do cliente: o botão estava certo quando foi desenhado. A resposta
    carrega para onde a interface deve levar a pessoa agora.
    """

    def __init__(
        self,
        current_action: str,
        plan_id: Optional[str] = None,
        recommendation_id: Optional[str] = None,
    ) -> None:
        super().__init__(f"Esta oportunidade já tem um registro: {current_action}.")
        self.current_action = current_action
        self.plan_id = plan_id
        self.recommendation_id = recommendation_id


class RegisterConversationRecommendationUseCase(_EngineBackedUseCase):
    """Registra uma recomendação nascida da conversa com a IA.

    Só é chamado por um gesto explícito do usuário ("Salvar como recomendação").
    Nenhuma resposta do agente vira registro sozinha.

    O cliente envia apenas as referências (conversa, mensagem, oportunidade): o
    conteúdo sai do bloco persistido. Aceitar assunto, diagnóstico ou evidências
    vindos do cliente deixaria o registro auditável à mercê de quem chama a
    rota — o snapshot gravado é a única versão que a IA de fato produziu.
    """

    def __init__(self, agent_message_repo: Any = None, conversation_repo: Any = None, **repos: Any) -> None:
        super().__init__(**repos)
        self._agent_message_repo = agent_message_repo
        self._conversation_repo = conversation_repo

    def execute(
        self,
        profile_id: str,
        currency: str,
        conversation_id: str,
        message_id: str,
        opportunity_id: str,
        now: Optional[datetime] = None,
    ) -> Recommendation:
        block = self._load_opportunity(profile_id, conversation_id, message_id, opportunity_id)
        topic = get_topic(block.topic)
        if topic is None:
            raise OpportunityNotFoundError(f"Assunto fora do catálogo: {block.topic!r}")

        # Revalidação no clique. `available_actions` do bloco é o retrato do que
        # foi exibido; entre a resposta e o clique pode ter surgido plano ou
        # recomendação para o mesmo assunto.
        plan_id = related_plan_id(self._plan_repo, profile_id, topic)
        if plan_id is not None:
            raise OpportunityActionOutdatedError("view_plan", plan_id=plan_id)

        existing_id = related_recommendation_id(
            self._repo, profile_id, topic, block.subject_key
        )
        if existing_id is not None:
            raise OpportunityActionOutdatedError("view_recommendation", recommendation_id=existing_id)

        return self._repo.add(
            Recommendation(
                id=str(uuid4()),
                profile_id=profile_id,
                kind=RecommendationKind.CONVERSATION_ADVICE,
                source=RecommendationSource.CONVERSATION,
                status=RecommendationStatus.PENDING,
                generated_at=now or datetime.utcnow(),
                payload=self._payload_from(block),
                input_fingerprint=self._fingerprint(profile_id, currency),
                scenario=ANALYSIS_SCENARIO,
                conversation_id=conversation_id,
                message_id=message_id,
            )
        )

    def _load_opportunity(
        self, profile_id: str, conversation_id: str, message_id: str, opportunity_id: str
    ):
        message = self._agent_message_repo.get(message_id)
        if message is None or message.conversation_id != conversation_id:
            raise OpportunityNotFoundError(f"Mensagem não encontrada: {message_id!r}")

        conversation = self._conversation_repo.get(conversation_id)
        if conversation is None or conversation.profile_id != profile_id:
            raise OpportunityNotFoundError(f"Conversa não encontrada: {conversation_id!r}")

        for raw in message.opportunities:
            if raw.get("id") == opportunity_id:
                return opportunity_blocks.from_dict(raw)
        raise OpportunityNotFoundError(f"Oportunidade não encontrada: {opportunity_id!r}")

    @staticmethod
    def _payload_from(block) -> dict[str, Any]:
        """O registro guarda o bloco como ele foi exibido.

        `topic` e `subject_key` ficam no payload porque é por eles que a próxima
        resposta reconhece que este assunto já está registrado.
        """
        assessment = block.assessment
        return {
            "status": "available",
            "topic": block.topic,
            "subject_key": block.subject_key,
            "opportunity_id": block.id,
            "summary": block.title,
            "diagnosis": block.diagnosis,
            "suggested_actions": list(block.suggested_actions),
            "evidence_references": list(block.evidence_references),
            "assessment": (
                {
                    "value": str(assessment.value) if assessment.value is not None else None,
                    "tier": assessment.tier,
                    "severity": assessment.severity,
                    "policy_id": assessment.policy_id,
                    "policy_version": assessment.policy_version,
                }
                if assessment is not None
                else None
            ),
        }
