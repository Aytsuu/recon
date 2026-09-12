from fastapi.testclient import TestClient

from app.repositories.memory import InMemoryCaseRepository
from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import (
    CaseStatus,
    ClarificationFieldKey,
    ClarificationStatus,
    InputMode,
)
from app.schemas.envelopes import NOT_IMPLEMENTED_CODE, NOT_IMPLEMENTED_MESSAGE

CASE_NOT_FOUND = {
    "error": {
        "code": "case_not_found",
        "message": "Case not found.",
    }
}

CLARIFICATION_NOT_FOUND = {
    "error": {
        "code": "clarification_not_found",
        "message": "Clarification not found.",
    }
}

NOT_IMPLEMENTED = {
    "error": {
        "code": NOT_IMPLEMENTED_CODE,
        "message": NOT_IMPLEMENTED_MESSAGE,
    }
}


def test_typed_creation_returns_input_ready(client: TestClient) -> None:
    response = client.post(
        "/api/cases",
        json={
            "input_mode": "typed",
            "case_text": "My internet keeps disconnecting.",
            "language_code": "en",
            "provider_name": "Converge ICT",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["input_mode"] == "typed"
    assert payload["status"] == "input_ready"
    assert payload["case_text"] == "My internet keeps disconnecting."
    assert payload["language_code"] == "en"
    assert payload["provider_name"] == "Converge ICT"
    assert payload["clarifications"] == []
    assert payload["draft"] is None


def test_voice_creation_returns_transcribing(client: TestClient) -> None:
    response = client.post("/api/cases", json={"input_mode": "voice"})

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["input_mode"] == "voice"
    assert payload["status"] == "transcribing"
    assert payload["case_text"] is None


def test_blank_typed_input_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": "   "},
    )

    assert response.status_code == 422


def test_get_existing_case_returns_complete_payload(client: TestClient) -> None:
    created = client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": "Problem"},
    ).json()["data"]

    response = client.get(f"/api/cases/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {"data": created}


def test_get_unknown_case_returns_case_not_found(client: TestClient) -> None:
    response = client.get("/api/cases/999")

    assert response.status_code == 404
    assert response.json() == CASE_NOT_FOUND


def test_reviewing_voice_transcript_moves_case_to_input_ready(client: TestClient) -> None:
    created = client.post("/api/cases", json={"input_mode": "voice"}).json()["data"]

    response = client.patch(
        f"/api/cases/{created['id']}",
        json={"case_text": "Reviewed transcript text."},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "input_ready"
    assert payload["case_text"] == "Reviewed transcript text."


def test_patch_persists_allowed_case_fields(client: TestClient) -> None:
    created = client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": "Problem"},
    ).json()["data"]

    response = client.patch(
        f"/api/cases/{created['id']}",
        json={
            "provider_name": "Converge ICT",
            "service_name": "Residential fiber internet",
            "issue_category": "internet_connectivity",
            "problem_summary": "Intermittent connection.",
            "attempted_resolutions": ["Restarted the router"],
            "desired_outcome": "Restore stable service",
            "language_code": "en",
        },
    )

    payload = response.json()["data"]
    assert payload["provider_name"] == "Converge ICT"
    assert payload["service_name"] == "Residential fiber internet"
    assert payload["issue_category"] == "internet_connectivity"
    assert payload["problem_summary"] == "Intermittent connection."
    assert payload["attempted_resolutions"] == ["Restarted the router"]
    assert payload["desired_outcome"] == "Restore stable service"
    assert payload["language_code"] == "en"


def test_material_edit_removes_draft_and_sets_ready_for_draft(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.draft_ready,
        case_text="Problem",
        provider_name="Converge ICT",
        problem_summary="Intermittent connection.",
        desired_outcome="Restore stable service",
    )
    repository.save_draft(
        created.id,
        DraftData(
            id=0,
            subject="Internet issue",
            body="Please help.",
            language_code="en",
        ),
    )

    response = client.patch(
        f"/api/cases/{created.id}",
        json={"problem_summary": "Connection drops every five minutes."},
    )

    payload = response.json()["data"]
    assert payload["draft"] is None
    assert payload["status"] == "ready_for_draft"
    assert payload["problem_summary"] == "Connection drops every five minutes."


def test_material_edit_without_required_fields_returns_input_ready(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.draft_ready,
        case_text="Problem",
        provider_name="Converge ICT",
    )
    repository.save_draft(
        created.id,
        DraftData(id=0, subject="Issue", body="Please help.", language_code="en"),
    )

    response = client.patch(
        f"/api/cases/{created.id}",
        json={"case_text": "Updated problem text."},
    )

    payload = response.json()["data"]
    assert payload["draft"] is None
    assert payload["status"] == "input_ready"


def test_answered_clarification_copies_answer_to_case_field(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.clarifying,
        case_text="Problem",
    )
    clarification = repository.create_or_update_clarification(
        created.id,
        ClarificationData(
            id=0,
            field_key=ClarificationFieldKey.provider_name,
            question="Which provider are you contacting?",
            answer=None,
            status=ClarificationStatus.pending,
            position=1,
        ),
    )

    response = client.patch(
        f"/api/cases/{created.id}/clarifications/{clarification.id}",
        json={"status": "answered", "answer": "Converge ICT"},
    )

    payload = response.json()["data"]
    assert payload["provider_name"] == "Converge ICT"
    assert payload["clarifications"][0]["status"] == "answered"
    assert payload["clarifications"][0]["answer"] == "Converge ICT"


def test_pending_clarification_keeps_case_clarifying(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.clarifying,
        case_text="Problem",
        problem_summary="Intermittent connection.",
    )
    first = repository.create_or_update_clarification(
        created.id,
        ClarificationData(
            id=0,
            field_key=ClarificationFieldKey.provider_name,
            question="Which provider?",
            answer=None,
            status=ClarificationStatus.pending,
            position=1,
        ),
    )
    repository.create_or_update_clarification(
        created.id,
        ClarificationData(
            id=0,
            field_key=ClarificationFieldKey.desired_outcome,
            question="What outcome do you want?",
            answer=None,
            status=ClarificationStatus.pending,
            position=2,
        ),
    )

    response = client.patch(
        f"/api/cases/{created.id}/clarifications/{first.id}",
        json={"status": "answered", "answer": "Converge ICT"},
    )

    payload = response.json()["data"]
    assert payload["status"] == "clarifying"
    assert any(item["status"] == "pending" for item in payload["clarifications"])


def test_resolving_final_clarification_moves_case_to_ready_for_draft(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.clarifying,
        case_text="Problem",
        provider_name="Converge ICT",
        problem_summary="Intermittent connection.",
    )
    clarification = repository.create_or_update_clarification(
        created.id,
        ClarificationData(
            id=0,
            field_key=ClarificationFieldKey.desired_outcome,
            question="What outcome do you want?",
            answer=None,
            status=ClarificationStatus.pending,
            position=1,
        ),
    )

    response = client.patch(
        f"/api/cases/{created.id}/clarifications/{clarification.id}",
        json={"status": "answered", "answer": "Restore stable service"},
    )

    payload = response.json()["data"]
    assert payload["status"] == "ready_for_draft"
    assert payload["desired_outcome"] == "Restore stable service"


def test_unknown_clarification_returns_not_found(
    client: TestClient,
    repository: InMemoryCaseRepository,
) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="Problem",
    )

    response = client.patch(
        f"/api/cases/{created.id}/clarifications/999",
        json={"status": "answered", "answer": "Converge ICT"},
    )

    assert response.status_code == 404
    assert response.json() == CLARIFICATION_NOT_FOUND


def test_deferred_routes_still_return_not_implemented(client: TestClient) -> None:
    created = client.post(
        "/api/cases",
        json={"input_mode": "typed", "case_text": "Problem"},
    ).json()["data"]

    deferred_routes = [
        (
            "POST",
            f"/api/cases/{created['id']}/transcribe",
            {"files": {"audio": ("a.webm", b"x", "audio/webm")}},
        ),
        ("POST", f"/api/cases/{created['id']}/extract", {}),
        ("POST", f"/api/cases/{created['id']}/draft", {}),
        (
            "PATCH",
            f"/api/cases/{created['id']}/draft",
            {"json": {"subject": "Subject", "body": "Body"}},
        ),
    ]

    for method, path, kwargs in deferred_routes:
        response = client.request(method, path, **kwargs)
        assert response.status_code == 501
        assert response.json() == NOT_IMPLEMENTED
