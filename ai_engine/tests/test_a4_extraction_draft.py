import pytest
from fastapi.testclient import TestClient

from app.schemas.enums import CaseStatus, ClarificationFieldKey, InputMode
from app.repositories.memory import InMemoryCaseRepository
from app.services.intelligence.fake import FakeCaseIntelligenceService
from app.services.intelligence.protocol import ExtractionResult
from app.services.intelligence.rule_based import RuleBasedCaseIntelligenceService

CASE_NOT_FOUND = {
    "error": {
        "code": "case_not_found",
        "message": "Case not found.",
    }
}

EXTRACT_INVALID_STATE = {
    "error": {
        "code": "invalid_case_state",
        "message": "Extraction is only available for cases in input_ready status.",
    }
}

DRAFT_INVALID_STATE = {
    "error": {
        "code": "invalid_case_state",
        "message": "Draft generation is only available for cases in ready_for_draft status.",
    }
}

DRAFT_NOT_FOUND = {
    "error": {
        "code": "draft_not_found",
        "message": "Draft not found.",
    }
}

CONVERGE_COMPLETE_TEXT = (
    "My Converge connection keeps dropping and the LOS light keeps blinking red. "
    "I want stable service restored."
)
CONVERGE_INCOMPLETE_TEXT = (
    "My Converge connection keeps dropping and the LOS light keeps blinking red."
)


def _create_input_ready_case(client: TestClient, case_text: str) -> dict:
    return client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": case_text},
    ).json()["data"]


def _create_ready_for_draft_case(
    repository: InMemoryCaseRepository,
    *,
    case_text: str = "Problem text",
) -> int:
    case = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.ready_for_draft,
        case_text=case_text,
        provider_name="Converge ICT",
        problem_summary="Intermittent internet connection.",
        desired_outcome="Restore stable service",
    )
    return case.id


@pytest.mark.asyncio
async def test_rule_based_adapter_extracts_converge_connectivity_example() -> None:
    service = RuleBasedCaseIntelligenceService()
    result = await service.extract(CONVERGE_COMPLETE_TEXT)

    assert result.provider_name == "Converge ICT"
    assert result.service_name == "Residential fiber internet"
    assert result.issue_category == "internet_connectivity"
    assert result.problem_summary == CONVERGE_COMPLETE_TEXT
    assert result.desired_outcome == "Restore stable service"
    assert result.missing_fields == ()


@pytest.mark.asyncio
async def test_rule_based_adapter_marks_incomplete_converge_case_for_clarification() -> None:
    service = RuleBasedCaseIntelligenceService()
    result = await service.extract(CONVERGE_INCOMPLETE_TEXT)

    assert result.provider_name == "Converge ICT"
    assert result.problem_summary == CONVERGE_INCOMPLETE_TEXT
    assert result.desired_outcome is None
    assert result.missing_fields == (ClarificationFieldKey.desired_outcome,)


def test_extraction_complete_case_produces_ready_for_draft(
    client: TestClient,
    fake_case_intelligence_service: FakeCaseIntelligenceService,
) -> None:
    fake_case_intelligence_service.set_result(
        ExtractionResult(
            provider_name="Converge ICT",
            service_name="Residential fiber internet",
            issue_category="internet_connectivity",
            problem_summary="Intermittent internet connection.",
            attempted_resolutions=("Restarted the router",),
            desired_outcome="Restore stable service",
            missing_fields=(),
        )
    )
    created = _create_input_ready_case(client, "My internet keeps disconnecting.")

    response = client.post(f"/api/cases/{created['id']}/extract")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ready_for_draft"
    assert payload["provider_name"] == "Converge ICT"
    assert payload["desired_outcome"] == "Restore stable service"
    assert payload["clarifications"] == []


def test_extraction_incomplete_case_produces_clarifying_questions(
    client: TestClient,
    fake_case_intelligence_service: FakeCaseIntelligenceService,
) -> None:
    fake_case_intelligence_service.set_result(
        ExtractionResult(
            provider_name="Converge ICT",
            problem_summary="Connection keeps dropping.",
            missing_fields=(ClarificationFieldKey.desired_outcome,),
        )
    )
    created = _create_input_ready_case(client, CONVERGE_INCOMPLETE_TEXT)

    response = client.post(f"/api/cases/{created['id']}/extract")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "clarifying"
    assert len(payload["clarifications"]) == 1
    clarification = payload["clarifications"][0]
    assert clarification["field_key"] == "desired_outcome"
    assert clarification["status"] == "pending"
    assert clarification["question"] == "What outcome would you like from support?"


def test_extraction_unknown_case_returns_not_found(client: TestClient) -> None:
    response = client.post("/api/cases/999/extract")

    assert response.status_code == 404
    assert response.json() == CASE_NOT_FOUND


def test_extraction_rejects_non_input_ready_case(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    case_id = _create_ready_for_draft_case(repository)

    response = client.post(f"/api/cases/{case_id}/extract")

    assert response.status_code == 409
    assert response.json() == EXTRACT_INVALID_STATE


def test_draft_generation_creates_draft_and_sets_draft_ready(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    case_id = _create_ready_for_draft_case(repository)

    response = client.post(f"/api/cases/{case_id}/draft")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "draft_ready"
    assert payload["draft"] is not None
    assert "Converge ICT" in payload["draft"]["subject"]
    assert "Intermittent internet connection." in payload["draft"]["body"]
    assert "Restore stable service" in payload["draft"]["body"]


def test_draft_generation_unknown_case_returns_not_found(client: TestClient) -> None:
    response = client.post("/api/cases/999/draft")

    assert response.status_code == 404
    assert response.json() == CASE_NOT_FOUND


def test_draft_generation_rejects_non_ready_for_draft_case(client: TestClient) -> None:
    created = _create_input_ready_case(client, "My internet keeps disconnecting.")

    response = client.post(f"/api/cases/{created['id']}/draft")

    assert response.status_code == 409
    assert response.json() == DRAFT_INVALID_STATE


def test_draft_update_persists_changes_and_returns_draft_ready(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    case_id = _create_ready_for_draft_case(repository)
    client.post(f"/api/cases/{case_id}/draft")

    response = client.patch(
        f"/api/cases/{case_id}/draft",
        json={
            "subject": "Updated subject",
            "body": "Updated body with more detail.",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "draft_ready"
    assert payload["draft"]["subject"] == "Updated subject"
    assert payload["draft"]["body"] == "Updated body with more detail."


def test_draft_update_without_existing_draft_returns_not_found(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    case_id = _create_ready_for_draft_case(repository)

    response = client.patch(
        f"/api/cases/{case_id}/draft",
        json={"subject": "Updated subject", "body": "Updated body"},
    )

    assert response.status_code == 404
    assert response.json() == DRAFT_NOT_FOUND


def test_extraction_and_draft_routes_are_no_longer_deferred(client: TestClient) -> None:
    created = _create_input_ready_case(client, CONVERGE_COMPLETE_TEXT)

    extract_response = client.post(f"/api/cases/{created['id']}/extract")
    assert extract_response.status_code == 200
    assert extract_response.json()["data"]["status"] == "ready_for_draft"

    draft_response = client.post(f"/api/cases/{created['id']}/draft")
    assert draft_response.status_code == 200
    assert draft_response.json()["data"]["status"] == "draft_ready"
