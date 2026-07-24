import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.persistence import models  # noqa: F401 - popula Base.metadata
from src.infrastructure.persistence.base import Base


@pytest.fixture()
def session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    db_session = session_factory()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture()
def client(session: Session) -> TestClient:
    from src.infrastructure.persistence.session import get_session
    from src.interfaces.http.main import app

    def _override_get_session():
        yield session

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
