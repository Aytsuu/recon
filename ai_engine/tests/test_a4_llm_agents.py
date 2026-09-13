import json
import os
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_case_intelligence_service,
    get_case_repository,
    get_draft_service,
)
from app.core.config import get_settings
from app.main import app
from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus, ClarificationFieldKey, InputMode
from app.services.draft import LLMDraftService, TemplateDraftService
from app.services.intelligence.llm_based import LLMCaseIntelligenceService
from app.services.llm.fake import FakeLLMClient
from app.services.llm.openai_client import OpenAILLMClient

VALID_EXTRACTION_JSON = json.dumps(
    {
        "provider_name": "Converge ICT",
        "service_name": "Residential fiber internet",
        "issue_category": "internet_connectivity",
        "problem_summary": "Intermittent internet connection with red LOS indicator.",
        "attempted_resolutions": ["Restarted the router"],
        "desired_outcome": "Restore stable service",
    }
)

VALID_DRAFT_JSON = json.dumps(
    {
        "subject": "Internet connectivity complaint – Converge ICT",
        "body": "Dear Converge ICT Support,\n\nMy connection keeps dropping.\n\nPlease restore service.",
    }
)


@pytest.mark.asyncio
async def test_llm_intelligence_service_parses_valid_json() -> None:
    service = LLMCaseIntelligenceService(FakeLLMClient(VALID_EXTRACTION_JSON))
    result = await service.extract("My Wi-Fi has a red LOS and my ISP is Converge.")

    assert result.provider_name == "Converge ICT"
    assert result.service_name == "Residential fiber internet"
    assert result.issue_category == "internet_connectivity"
    assert result.problem_summary == "Intermittent internet connection with red LOS indicator."
    assert result.attempted_resolutions == ("Restarted the router",)
    assert result.desired_outcome == "Restore stable service"
    assert result.missing_fields == ()


@pytest.mark.asyncio
async def test_llm_intelligence_service_falls_back_on_malformed_json() -> None:
    service = LLMCaseIntelligenceService(FakeLLMClient("not-json"))
    result = await service.extract("Problem description")

    assert result.provider_name is None
    assert result.problem_summary is None
    assert result.desired_outcome is None
    assert result.missing_fields == (
        ClarificationFieldKey.provider_name,
        ClarificationFieldKey.problem_summary,
        ClarificationFieldKey.desired_outcome,
    )


@pytest.mark.asyncio
async def test_llm_draft_service_parses_valid_json(repository: InMemoryCaseRepository) -> None:
    case = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.ready_for_draft,
        case_text="Problem",
        provider_name="Converge ICT",
        problem_summary="Intermittent internet connection.",
        desired_outcome="Restore stable service",
    )
    service = LLMDraftService(FakeLLMClient(VALID_DRAFT_JSON))
    draft = await service.compose(case)

    assert draft.subject == "Internet connectivity complaint – Converge ICT"
    assert "Dear Converge ICT Support" in draft.body


@pytest.mark.asyncio
async def test_llm_draft_service_falls_back_to_template_on_malformed_json(
    repository: InMemoryCaseRepository,
) -> None:
    case = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.ready_for_draft,
        case_text="Problem",
        provider_name="Converge ICT",
        problem_summary="Intermittent internet connection.",
        desired_outcome="Restore stable service",
    )
    service = LLMDraftService(FakeLLMClient("not-json"))
    draft = await service.compose(case)

    assert draft.subject == "Support complaint – Converge ICT"
    assert "Intermittent internet connection." in draft.body
    assert "Restore stable service" in draft.body


@pytest.mark.asyncio
async def test_openai_client_uses_bearer_auth_and_parses_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"provider_name": "Converge ICT"}'}}]},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    service = OpenAILLMClient(api_key="test-key", model="gpt-4o-mini", client=client)

    content = await service.complete("system", "prompt")

    assert content == '{"provider_name": "Converge ICT"}'


def test_dependency_selection_without_openai_key() -> None:
    get_settings.cache_clear()
    with patch.dict(os.environ, {"AI_ENGINE_OPENAI_API_KEY": ""}, clear=False):
        get_settings.cache_clear()
        from app.api.dependencies import get_case_intelligence_service, get_draft_service

        intelligence = get_case_intelligence_service()
        draft = get_draft_service()

        assert intelligence.__class__.__name__ == "RuleBasedCaseIntelligenceService"
        assert isinstance(draft, TemplateDraftService)


def test_dependency_selection_with_openai_key() -> None:
    get_settings.cache_clear()
    with patch.dict(os.environ, {"AI_ENGINE_OPENAI_API_KEY": "test-key"}, clear=False):
        get_settings.cache_clear()
        from app.api.dependencies import get_case_intelligence_service, get_draft_service

        intelligence = get_case_intelligence_service()
        draft = get_draft_service()

        assert intelligence.__class__.__name__ == "LLMCaseIntelligenceService"
        assert isinstance(draft, LLMDraftService)
        assert intelligence._llm_client._api_key == "test-key"
        assert draft._llm_client._api_key == "test-key"


def test_extract_and_draft_routes_use_llm_services(
    repository: InMemoryCaseRepository,
) -> None:
    extraction_client = FakeLLMClient(VALID_EXTRACTION_JSON)
    draft_client = FakeLLMClient(VALID_DRAFT_JSON)

    app.dependency_overrides[get_case_repository] = lambda: repository
    app.dependency_overrides[get_case_intelligence_service] = lambda: LLMCaseIntelligenceService(
        extraction_client
    )
    app.dependency_overrides[get_draft_service] = lambda: LLMDraftService(draft_client)

    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/cases",
                json={
                    "input_mode": "typed",
                    "case_text": "My Wi-Fi has a red LOS and my ISP is Converge.",
                },
            ).json()["data"]

            extract_response = client.post(f"/api/cases/{created['id']}/extract")
            assert extract_response.status_code == 200
            extracted = extract_response.json()["data"]
            assert extracted["status"] == "ready_for_draft"
            assert extracted["provider_name"] == "Converge ICT"
            assert extracted["desired_outcome"] == "Restore stable service"

            draft_response = client.post(f"/api/cases/{created['id']}/draft")
            assert draft_response.status_code == 200
            drafted = draft_response.json()["data"]
            assert drafted["status"] == "draft_ready"
            assert drafted["draft"]["subject"] == "Internet connectivity complaint – Converge ICT"
            assert "Dear Converge ICT Support" in drafted["draft"]["body"]
    finally:
        app.dependency_overrides.pop(get_case_repository, None)
        app.dependency_overrides.pop(get_case_intelligence_service, None)
        app.dependency_overrides.pop(get_draft_service, None)
        get_settings.cache_clear()
