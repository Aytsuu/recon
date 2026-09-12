import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_case_repository
from app.main import app
from app.repositories.memory import InMemoryCaseRepository

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def repository() -> InMemoryCaseRepository:
    return InMemoryCaseRepository()


@pytest.fixture
def client(repository: InMemoryCaseRepository) -> TestClient:
    app.dependency_overrides[get_case_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
