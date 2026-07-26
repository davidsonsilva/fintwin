from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.agent.entities import Conversation
from src.infrastructure.persistence.models import ConversationModel


def _to_model(conversation: Conversation) -> ConversationModel:
    return ConversationModel(
        id=conversation.id,
        profile_id=conversation.profile_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _to_entity(model: ConversationModel) -> Conversation:
    return Conversation(
        id=model.id,
        profile_id=model.profile_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyConversationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, conversation: Conversation) -> None:
        self._session.add(_to_model(conversation))
        self._session.commit()

    def get(self, conversation_id: str) -> Optional[Conversation]:
        model = self._session.get(ConversationModel, conversation_id)
        return _to_entity(model) if model is not None else None

    def update(self, conversation: Conversation) -> None:
        self._session.merge(_to_model(conversation))
        self._session.commit()
