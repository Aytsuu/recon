from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_case_repository
from app.api.responses import case_not_found_response, case_success_response
from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus, InputMode
from app.schemas.requests import CreateCaseRequest, UpdateCaseRequest
from app.services.case_state import apply_case_patch

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", status_code=201)
def create_case(
    payload: CreateCaseRequest,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
):
    if payload.input_mode == InputMode.typed:
        status = CaseStatus.input_ready
        case_text = payload.case_text
    else:
        status = CaseStatus.transcribing
        case_text = None

    case = repository.create_case(
        input_mode=payload.input_mode,
        status=status,
        case_text=case_text,
        language_code=payload.language_code,
        provider_name=payload.provider_name,
    )
    return case_success_response(case, status_code=201)


@router.get("/{case_id}")
def get_case(
    case_id: int,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()
    return case_success_response(case)


@router.patch("/{case_id}")
def update_case(
    case_id: int,
    payload: UpdateCaseRequest,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return case_success_response(case)

    patched = apply_case_patch(case, updates)
    patch_fields = patched.model_dump(mode="python")
    patch_fields.pop("id")
    updated = repository.update_case(case_id, **patch_fields)
    return case_success_response(updated)
