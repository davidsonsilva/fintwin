from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.interfaces.http.rate_limit import RateLimiter


def _fake_request(host: str = "1.2.3.4"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


def test_allows_requests_under_the_limit() -> None:
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    request = _fake_request()

    for _ in range(3):
        limiter(request)


def test_blocks_requests_over_the_limit() -> None:
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    request = _fake_request()

    limiter(request)
    limiter(request)
    with pytest.raises(HTTPException) as exc_info:
        limiter(request)
    assert exc_info.value.status_code == 429


def test_tracks_clients_independently() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter(_fake_request(host="1.1.1.1"))
    limiter(_fake_request(host="2.2.2.2"))  # não deve ser bloqueado pelo hit do outro IP


def test_window_expiry_releases_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=10)
    request = _fake_request()

    fake_now = [1000.0]
    monkeypatch.setattr("time.monotonic", lambda: fake_now[0])

    limiter(request)
    with pytest.raises(HTTPException):
        limiter(request)

    fake_now[0] += 11
    limiter(request)  # janela expirou, deve liberar de novo
