# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.domain.agent.entities import AgentMessage
from src.infrastructure.persistence.models import AgentMessageModel


def _to_model(message: AgentMessage) -> AgentMessageModel:
    return AgentMessageModel(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        tool_calls=list(message.tool_calls),
        pending_action=dict(message.pending_action) if message.pending_action is not None else None,
        confirmed=message.confirmed,
        created_at=message.created_at,
    )


def _to_entity(model: AgentMessageModel) -> AgentMessage:
    return AgentMessage(
        id=model.id,
        conversation_id=model.conversation_id,
        role=model.role,
        content=model.content,
        tool_calls=list(model.tool_calls),
        pending_action=dict(model.pending_action) if model.pending_action is not None else None,
        confirmed=model.confirmed,
        created_at=model.created_at,
    )


class SqlAlchemyAgentMessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, message: AgentMessage) -> None:
        self._session.add(_to_model(message))
        self._session.commit()

    def get(self, message_id: str) -> Optional[AgentMessage]:
        model = self._session.get(AgentMessageModel, message_id)
        return _to_entity(model) if model is not None else None

    def list_by_conversation(self, conversation_id: str) -> list[AgentMessage]:
        stmt = (
            select(AgentMessageModel)
            .where(AgentMessageModel.conversation_id == conversation_id)
            .order_by(AgentMessageModel.created_at)
        )
        models = self._session.execute(stmt).scalars().all()
        return [_to_entity(model) for model in models]

    def update(self, message: AgentMessage) -> None:
        self._session.merge(_to_model(message))
        self._session.commit()

    def try_claim(self, message_id: str) -> bool:
        """Marca `confirmed=True` de forma atômica, só se ainda não estava confirmado.

        Usa um UPDATE condicional (WHERE confirmed=false) em vez de ler-e-escrever,
        para que duas confirmações concorrentes da mesma ação nunca persistam a
        simulação duas vezes (achado do Meta Harness na VS-09).

        Deliberadamente NÃO comita aqui: o caller (`ConfirmPendingActionUseCase`)
        persiste a simulação na mesma sessão logo em seguida, e é esse commit
        posterior que também efetiva este claim. Se qualquer passo entre o claim
        e a persistência da simulação falhar, a sessão é fechada sem commit
        (`get_session`) e o claim é descartado — a ação volta a ficar disponível
        para uma nova tentativa, em vez de ficar presa como "confirmada" sem
        nenhuma simulação correspondente (achado do Meta Harness na VS-09).
        """
        stmt = (
            update(AgentMessageModel)
            .where(AgentMessageModel.id == message_id, AgentMessageModel.confirmed.is_(False))
            .values(confirmed=True)
        )
        result = self._session.execute(stmt)
        return result.rowcount == 1
