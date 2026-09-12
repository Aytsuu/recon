import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_case_repository, get_streaming_token_service
from app.core.config import get_settings
from app.main import app
from app.repositories.memory import InMemoryCaseRepository
from app.services.transcription.fake import FakeStreamingTokenService

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def repository() -> InMemoryCaseRepository:
    return InMemoryCaseRepository()


@pytest.fixture
def fake_streaming_token_service() -> FakeStreamingTokenService:
    return FakeStreamingTokenService()


@pytest.fixture
def client(
    repository: InMemoryCaseRepository,
    fake_streaming_token_service: FakeStreamingTokenService,
) -> TestClient:
    app.dependency_overrides[get_case_repository] = lambda: repository
    app.dependency_overrides[get_streaming_token_service] = lambda: fake_streaming_token_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
