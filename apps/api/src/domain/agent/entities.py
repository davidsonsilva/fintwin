"""Entidades do agente conversacional (Spec seções 6.8, 18.11 e 24)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from src.domain.shared.enums import MessageRole


@dataclass
class Conversation:
    id: str
    profile_id: str
    created_at: datetime
    updated_at: datetime


@dataclass
class AgentMessage:
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime
    tool_calls: Sequence[Mapping[str, Any]] = field(default_factory=list)
    pending_action: Optional[Mapping[str, Any]] = None
    confirmed: bool = False

    def __post_init__(self) -> None:
        if not self.content and not self.tool_calls:
            raise ValueError("AgentMessage requer content ou tool_calls.")
