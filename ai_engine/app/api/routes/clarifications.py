from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_case_repository
from app.api.responses import (
    case_not_found_response,
    case_success_response,
    clarification_not_found_response,
)
from app.repositories.memory import InMemoryCaseRepository
from app.schemas.requests import UpdateClarificationRequest
from app.services.case_state import apply_clarification_update

router = APIRouter(tags=["clarifications"])


@router.patch("/cases/{case_id}/clarifications/{clarification_id}")
def update_clarification(
    case_id: int,
    clarification_id: int,
    payload: UpdateClarificationRequest,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    clarification = next(
        (item for item in case.clarifications if item.id == clarification_id),
        None,
    )
    if clarification is None:
        return clarification_not_found_response()

    patched = apply_clarification_update(
        case,
        clarification,
        payload.status,
        payload.answer,
    )
    patch_fields = patched.model_dump(mode="python")
    patch_fields.pop("id")
    updated = repository.update_case(case_id, **patch_fields)
    return case_success_response(updated)
