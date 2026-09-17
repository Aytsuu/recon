from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_case_intelligence_service, get_case_repository
from app.api.responses import (
    case_not_found_response,
    case_success_response,
    invalid_case_state_response,
)
from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus
from app.services.extraction import apply_extraction
from app.services.intelligence.protocol import CaseIntelligenceService

router = APIRouter(tags=["extraction"])


@router.post("/cases/{case_id}/extract")
async def extract_case(
    case_id: int,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
    intelligence_service: Annotated[
        CaseIntelligenceService, Depends(get_case_intelligence_service)
    ],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    if case.status != CaseStatus.input_ready:
        return invalid_case_state_response(
            "Extraction is only available for cases in input_ready status."
        )

    if case.case_text is None or case.case_text.strip() == "":
        return invalid_case_state_response(
            "Extraction requires non-blank case_text in input_ready status."
        )

    result = await intelligence_service.extract(case.case_text)
    updated = apply_extraction(case, result, repository)
    return case_success_response(updated)
