# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Wrapper fino sobre a API da Anthropic para o agente conversacional (Spec seção 25).

`system` e as mensagens do usuário são sempre parâmetros separados na chamada à
API — nunca concatenados em uma única string — para satisfazer a exigência de
"separação entre mensagem do usuário e instruções de sistema".
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

import anthropic

DEFAULT_AGENT_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 1024


def get_agent_model() -> str:
    return os.environ.get("AGENT_MODEL", DEFAULT_AGENT_MODEL)


class AnthropicAgentClient:
    """Chamada única (não-streaming) à API de mensagens da Anthropic com tool calling."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._model = model or get_agent_model()

    def create_message(
        self,
        system: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
    ) -> Any:
        return self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            system=system,
            messages=list(messages),
            tools=list(tools),
        )
