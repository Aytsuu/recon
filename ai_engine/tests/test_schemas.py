import pytest
from pydantic import ValidationError

from app.schemas.case import CaseData
from app.schemas.envelopes import ErrorEnvelope, SuccessEnvelope
from app.schemas.requests import CreateCaseRequest, UpdateClarificationRequest
from tests.conftest import load_fixture

VALID_CASE_FIXTURES = [
    "input_ready_typed_case.json",
    "transcribing_voice_case.json",
    "clarifying_case_with_pending.json",
    "draft_ready_case_with_draft.json",
]


@pytest.mark.parametrize("fixture_name", VALID_CASE_FIXTURES)
def test_valid_case_fixtures_parse(fixture_name: str) -> None:
    payload = load_fixture(fixture_name)
    case = CaseData.model_validate(payload)
    serialized = case.model_dump(mode="json")

    assert serialized["input_mode"] == payload["input_mode"]
    assert serialized["status"] == payload["status"]
    assert list(serialized.keys()) == list(payload.keys())


def test_case_data_serializes_snake_case_fields() -> None:
    case = CaseData.model_validate(load_fixture("input_ready_typed_case.json"))
    serialized = case.model_dump(mode="json")

    assert set(serialized) == {
        "id",
        "input_mode",
        "status",
        "case_text",
        "language_code",
        "provider_name",
        "service_name",
        "issue_category",
        "problem_summary",
        "attempted_resolutions",
        "desired_outcome",
        "clarifications",
        "draft",
    }


def test_success_envelope_uses_data_key() -> None:
    case = CaseData.model_validate(load_fixture("input_ready_typed_case.json"))
    envelope = SuccessEnvelope[CaseData](data=case)

    assert envelope.model_dump(mode="json") == {"data": case.model_dump(mode="json")}


def test_error_envelope_matches_contract() -> None:
    envelope = ErrorEnvelope(
        error={
            "code": "not_implemented",
            "message": "This endpoint is reserved for a later implementation phase.",
        }
    )

    assert envelope.model_dump(mode="json") == {
        "error": {
            "code": "not_implemented",
            "message": "This endpoint is reserved for a later implementation phase.",
        }
    }


def test_create_case_request_rejects_blank_typed_case_text() -> None:
    payload = load_fixture("malformed_blank_typed_input.json")

    with pytest.raises(ValidationError):
        CreateCaseRequest.model_validate(payload)


def test_create_case_request_rejects_invalid_enum() -> None:
    with pytest.raises(ValidationError):
        CreateCaseRequest.model_validate({"input_mode": "invalid", "case_text": "Problem"})


def test_update_clarification_request_rejects_blank_answer_for_answered_status() -> None:
    payload = load_fixture("malformed_clarification_update.json")

    with pytest.raises(ValidationError):
        UpdateClarificationRequest.model_validate(payload)


def test_update_clarification_request_rejects_answer_for_skipped_status() -> None:
    with pytest.raises(ValidationError):
        UpdateClarificationRequest.model_validate(
            {"status": "skipped", "answer": "Should not be here"}
        )
