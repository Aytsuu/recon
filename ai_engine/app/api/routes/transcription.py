from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_case_repository, get_streaming_token_service
from app.api.responses import (
    case_not_found_response,
    invalid_case_state_response,
    token_issuance_failed_response,
    token_issuance_success_response,
    token_service_unavailable_response,
)
from app.repositories.memory import InMemoryCaseRepository
from app.schemas.enums import CaseStatus, InputMode
from app.schemas.transcription import TranscriptionTokenResponseData
from app.services.transcription.errors import TokenIssuanceFailedError, TokenServiceUnavailableError
from app.services.transcription.protocol import (
    DEFAULT_TOKEN_EXPIRES_IN_SECONDS,
    StreamingTokenService,
)

router = APIRouter(tags=["transcription"])


@router.post("/cases/{case_id}/transcription-token")
async def issue_transcription_token(
    case_id: int,
    repository: Annotated[InMemoryCaseRepository, Depends(get_case_repository)],
    streaming_token_service: Annotated[StreamingTokenService, Depends(get_streaming_token_service)],
):
    case = repository.get_case(case_id)
    if case is None:
        return case_not_found_response()

    if case.input_mode != InputMode.voice or case.status != CaseStatus.transcribing:
        return invalid_case_state_response()

    try:
        result = await streaming_token_service.issue_token(DEFAULT_TOKEN_EXPIRES_IN_SECONDS)
    except TokenServiceUnavailableError:
        return token_service_unavailable_response()
    except TokenIssuanceFailedError:
        return token_issuance_failed_response()

    return token_issuance_success_response(
        TranscriptionTokenResponseData(
            case_id=case_id,
            token=result.token,
            expires_in_seconds=result.expires_in_seconds,
        )
    )
