"""Rate limit básico em memória para endpoints sensíveis (Spec VS-10, seção 31).

Implementação simples de janela fixa por IP do cliente — suficiente para um
MVP monólito de processo único; não sobrevive a múltiplos workers/replicas
nem a reinícios (não é o objetivo aqui, apenas mitigar abuso trivial do
endpoint que chama a API paga da Anthropic).
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def __call__(self, request: Request) -> None:
        client_key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self._window_seconds

        hits = self._hits[client_key]
        while hits and hits[0] < window_start:
            hits.pop(0)

        if len(hits) >= self._max_requests:
            raise HTTPException(status_code=429, detail="Muitas requisições. Tente novamente em instantes.")

        hits.append(now)


agent_message_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
