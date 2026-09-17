from fastapi.testclient import TestClient

from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus, InputMode
from app.services.extraction import apply_extraction
from app.services.intelligence.fake import FakeCaseIntelligenceService
from app.services.intelligence.protocol import ExtractionResult


def test_apply_extraction_hydrates_support_contact_for_known_provider(
    repository: InMemoryCaseRepository,
) -> None:
    case = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="My Converge connection keeps dropping.",
    )
    result = ExtractionResult(
        provider_name="Converge ICT",
        service_name="Residential fiber internet",
        issue_category="internet_connectivity",
        problem_summary="Intermittent internet connection.",
        desired_outcome="Restore stable service",
        missing_fields=(),
    )

    updated = apply_extraction(case, result, repository)

    assert updated.support_email == "support@converge.com.ph"
    assert updated.support_phone == "1-800-1888-8388"
    assert updated.support_url == "https://www.converge.com.ph/support"


def test_apply_extraction_leaves_support_contact_none_for_unknown_provider(
    repository: InMemoryCaseRepository,
) -> None:
    case = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="My connection keeps dropping.",
    )
    result = ExtractionResult(
        provider_name="Unknown Provider XYZ",
        problem_summary="Connection issue.",
        desired_outcome="Fix the issue",
        missing_fields=(),
    )

    updated = apply_extraction(case, result, repository)

    assert updated.support_email is None
    assert updated.support_phone is None
    assert updated.support_url is None


def test_extract_route_returns_support_email_for_converge_case(
    client: TestClient,
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
    created = client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": "My Converge connection keeps dropping."},
    ).json()["data"]

    response = client.post(f"/api/cases/{created['id']}/extract")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["support_email"] == "support@converge.com.ph"
    assert payload["support_phone"] == "1-800-1888-8388"
    assert payload["support_url"] == "https://www.converge.com.ph/support"
