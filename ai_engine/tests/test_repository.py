from app.repositories.memory import InMemoryCaseRepository
from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import (
    CaseStatus,
    ClarificationFieldKey,
    ClarificationStatus,
    InputMode,
)
from tests.conftest import load_fixture


def test_repository_create_and_get_case(repository: InMemoryCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="My internet keeps disconnecting.",
    )
    loaded = repository.get_case(created.id)

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.case_text == "My internet keeps disconnecting."
    assert loaded is not created


def test_repository_update_case_returns_copy(repository: InMemoryCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.voice,
        status=CaseStatus.transcribing,
    )
    updated = repository.update_case(created.id, case_text="Reviewed transcript")
    original = repository.get_case(created.id)

    assert updated.case_text == "Reviewed transcript"
    assert original is not None
    assert original.case_text == "Reviewed transcript"
    assert updated is not original


def test_repository_manage_clarifications(repository: InMemoryCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.clarifying,
        case_text="Problem",
    )
    clarification = ClarificationData(
        id=0,
        field_key=ClarificationFieldKey.provider_name,
        question="Which provider are you contacting?",
        answer=None,
        status=ClarificationStatus.pending,
        position=1,
    )

    stored = repository.create_or_update_clarification(created.id, clarification)
    listed = repository.list_clarifications(created.id)

    assert stored.id == 1
    assert len(listed) == 1
    assert listed[0].question == clarification.question
    assert listed[0] is not stored


def test_repository_save_get_and_delete_draft(repository: InMemoryCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.draft_ready,
        case_text="Problem",
    )
    draft = DraftData(
        id=0,
        subject="Internet connectivity issue",
        body="Hello support.",
        language_code="en",
    )

    saved = repository.save_draft(created.id, draft)
    loaded = repository.get_draft(created.id)

    assert saved.id == 1
    assert loaded is not None
    assert loaded.body == "Hello support."
    assert loaded is not saved

    repository.delete_draft(created.id)
    assert repository.get_draft(created.id) is None


def test_repository_delete_case_removes_data(repository: InMemoryCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="Problem",
    )

    repository.delete_case(created.id)

    assert repository.get_case(created.id) is None


def test_repository_instances_do_not_share_state() -> None:
    first = InMemoryCaseRepository()
    second = InMemoryCaseRepository()

    created = first.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="Only in first repository",
    )

    assert first.get_case(created.id) is not None
    assert second.get_case(created.id) is None


def test_repository_accepts_shared_fixture_shape(repository: InMemoryCaseRepository) -> None:
    payload = load_fixture("draft_ready_case_with_draft.json")
    draft_payload = payload["draft"]
    assert draft_payload is not None

    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.draft_ready,
        case_text=payload["case_text"],
        language_code=payload["language_code"],
        provider_name=payload["provider_name"],
        service_name=payload["service_name"],
        issue_category=payload["issue_category"],
        problem_summary=payload["problem_summary"],
        attempted_resolutions=payload["attempted_resolutions"],
        desired_outcome=payload["desired_outcome"],
    )
    saved_draft = repository.save_draft(
        created.id,
        DraftData(
            id=0,
            subject=draft_payload["subject"],
            body=draft_payload["body"],
            language_code=draft_payload["language_code"],
        ),
    )

    loaded = repository.get_case(created.id)
    assert loaded is not None
    assert loaded.draft is not None
    assert loaded.draft.subject == saved_draft.subject
