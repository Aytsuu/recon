from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_case_intelligence_service,
    get_case_repository,
    get_draft_service,
)
from app.api.responses import (
    case_not_found_response,
    case_success_response,
    invalid_case_state_response,
)
from app.repositories.protocol import CaseRepository
from app.schemas.enums import CaseStatus, InputMode
from app.schemas.requests import ProcessVoiceRequest
from app.services.case_processing import process_case_intelligence
from app.services.draft import DraftService
from app.services.intelligence.protocol import CaseIntelligenceService

router = APIRouter(tags=["processing"])


@router.post("/cases/{case_id}/process-voice")
async def process_voice_case(
    case_id: int,
    payload: ProcessVoiceRequest,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    intelligence_service: Annotated[
        CaseIntelligenceService, Depends(get_case_intelligence_service)
    ],
    draft_service: Annotated[DraftService, Depends(get_draft_service)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    if case.input_mode != InputMode.voice:
        return invalid_case_state_response("Voice processing is only available for voice cases.")

    if case.status not in {CaseStatus.transcribing, CaseStatus.input_ready}:
        return invalid_case_state_response(
            "Voice processing is only available for cases in transcribing or input_ready status."
        )

    repository.update_case(
        case_id,
        case_text=payload.case_text.strip(),
        status=CaseStatus.input_ready,
    )
    refreshed = repository.get_case(case_id)
    if refreshed is None:
        return case_not_found_response()

    updated = await process_case_intelligence(
        refreshed,
        repository,
        intelligence_service,
        draft_service,
    )
    return case_success_response(updated)


@router.post("/cases/{case_id}/process")
async def process_case(
    case_id: int,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    intelligence_service: Annotated[
        CaseIntelligenceService, Depends(get_case_intelligence_service)
    ],
    draft_service: Annotated[DraftService, Depends(get_draft_service)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    if case.status != CaseStatus.input_ready:
        return invalid_case_state_response(
            "Processing is only available for cases in input_ready status."
        )

    if case.case_text is None or case.case_text.strip() == "":
        return invalid_case_state_response(
            "Processing requires non-blank case_text in input_ready status."
        )

    updated = await process_case_intelligence(
        case,
        repository,
        intelligence_service,
        draft_service,
    )
    return case_success_response(updated)
