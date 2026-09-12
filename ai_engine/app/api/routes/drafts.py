from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_case_repository
from app.api.responses import (
    case_not_found_response,
    case_success_response,
    draft_not_found_response,
    invalid_case_state_response,
)
from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus
from app.schemas.requests import UpdateDraftRequest
from app.services.draft import compose_draft

router = APIRouter(tags=["drafts"])


@router.post("/cases/{case_id}/draft")
def generate_draft(
    case_id: int,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    if case.status != CaseStatus.ready_for_draft:
        return invalid_case_state_response(
            "Draft generation is only available for cases in ready_for_draft status."
        )

    draft = compose_draft(case)
    repository.save_draft(case_id, draft)
    updated = repository.update_case(case_id, status=CaseStatus.draft_ready)
    return case_success_response(updated)


@router.patch("/cases/{case_id}/draft")
def update_draft(
    case_id: int,
    payload: UpdateDraftRequest,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    if case.draft is None:
        return draft_not_found_response()

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return case_success_response(case)

    draft = case.draft.model_copy(update=updates, deep=True)
    repository.save_draft(case_id, draft)
    updated = repository.update_case(case_id, status=CaseStatus.draft_ready, draft=draft)
    return case_success_response(updated)
