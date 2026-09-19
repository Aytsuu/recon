from fastapi.testclient import TestClient

from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus, InputMode
from app.services.intelligence.fake import FakeCaseIntelligenceService
from app.services.intelligence.protocol import ExtractionResult


def test_process_voice_runs_extract_and_draft(
    client: TestClient,
    repository: InMemoryCaseRepository,
    fake_case_intelligence_service: FakeCaseIntelligenceService,
) -> None:
    fake_case_intelligence_service.set_result(
        ExtractionResult(
            provider_name="Converge ICT",
            service_name="Residential fiber internet",
            issue_category="internet_connectivity",
            problem_summary="Intermittent internet connection.",
            desired_outcome="Restore stable service",
            missing_fields=(),
        )
    )
    case = repository.create_case(
        input_mode=InputMode.voice,
        status=CaseStatus.transcribing,
    )

    response = client.post(
        f"/api/cases/{case.id}/process-voice",
        json={"case_text": "My Converge connection keeps dropping."},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "draft_ready"
    assert payload["case_text"] == "My Converge connection keeps dropping."
    assert payload["provider_name"] == "Converge ICT"
    assert payload["support_email"] == "support@converge.com.ph"
    assert payload["draft"] is not None


def test_process_case_for_typed_input_ready(
    client: TestClient,
    repository: InMemoryCaseRepository,
    fake_case_intelligence_service: FakeCaseIntelligenceService,
) -> None:
    fake_case_intelligence_service.set_result(
        ExtractionResult(
            provider_name="Converge ICT",
            problem_summary="Connection issue.",
            desired_outcome="Fix the issue",
            missing_fields=(),
        )
    )
    case = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="My internet keeps dropping.",
    )

    response = client.post(f"/api/cases/{case.id}/process")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "draft_ready"
    assert payload["draft"] is not None
