import os

import pytest

from app.repositories.supabase import SupabaseCaseRepository
from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import (
    CaseStatus,
    ClarificationFieldKey,
    ClarificationStatus,
    InputMode,
)

pytestmark = pytest.mark.integration

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    pytest.skip(
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required for integration tests",
        allow_module_level=True,
    )


@pytest.fixture
def repository() -> SupabaseCaseRepository:
    return SupabaseCaseRepository.from_credentials(SUPABASE_URL, SUPABASE_KEY)


def test_supabase_create_and_get_case(repository: SupabaseCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.input_ready,
        case_text="Integration test case.",
        provider_name="Converge ICT",
    )
    try:
        loaded = repository.get_case(created.id)
        assert loaded is not None
        assert loaded.case_text == "Integration test case."
        assert loaded.provider_name == "Converge ICT"
    finally:
        repository.delete_case(created.id)


def test_supabase_clarification_and_draft_round_trip(repository: SupabaseCaseRepository) -> None:
    created = repository.create_case(
        input_mode=InputMode.typed,
        status=CaseStatus.clarifying,
        case_text="Problem text",
    )
    try:
        repository.create_or_update_clarification(
            created.id,
            ClarificationData(
                id=0,
                field_key=ClarificationFieldKey.provider_name,
                question="Which provider?",
                status=ClarificationStatus.pending,
                position=1,
            ),
        )
        repository.save_draft(
            created.id,
            DraftData(id=0, subject="Subject", body="Body", language_code="en"),
        )
        loaded = repository.get_case(created.id)
        assert loaded is not None
        assert len(loaded.clarifications) == 1
        assert loaded.draft is not None
        assert loaded.draft.subject == "Subject"
    finally:
        repository.delete_case(created.id)
