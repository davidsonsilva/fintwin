# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Interfaces de repositório para Conversation e AgentMessage (Spec seção 24)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.agent.entities import AgentMessage, Conversation


class ConversationRepository(Protocol):
    def add(self, conversation: Conversation) -> None: ...
    def get(self, conversation_id: str) -> Optional[Conversation]: ...
    def update(self, conversation: Conversation) -> None: ...


class AgentMessageRepository(Protocol):
    def add(self, message: AgentMessage) -> None: ...
    def get(self, message_id: str) -> Optional[AgentMessage]: ...
    def list_by_conversation(self, conversation_id: str) -> list[AgentMessage]: ...
    def update(self, message: AgentMessage) -> None: ...
    def try_claim(self, message_id: str) -> bool: ...
