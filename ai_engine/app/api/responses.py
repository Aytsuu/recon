from fastapi.responses import JSONResponse

from app.schemas.case import CaseData
from app.schemas.envelopes import NOT_IMPLEMENTED_CODE, NOT_IMPLEMENTED_MESSAGE
from app.schemas.transcription import TranscriptionTokenResponseData


def not_implemented_response() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "error": {
                "code": NOT_IMPLEMENTED_CODE,
                "message": NOT_IMPLEMENTED_MESSAGE,
            }
        },
    )


def case_not_found_response() -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "case_not_found",
                "message": "Case not found.",
            }
        },
    )


def clarification_not_found_response() -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "clarification_not_found",
                "message": "Clarification not found.",
            }
        },
    )


def case_success_response(case: CaseData, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"data": case.model_dump(mode="json")},
    )


def invalid_case_state_response(
    message: str = "The case is not in a valid state for this operation.",
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "code": "invalid_case_state",
                "message": message,
            }
        },
    )


def draft_not_found_response() -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "draft_not_found",
                "message": "Draft not found.",
            }
        },
    )


def token_issuance_failed_response() -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={
            "error": {
                "code": "token_issuance_failed",
                "message": "Streaming token could not be issued.",
            }
        },
    )


def token_service_unavailable_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "token_service_unavailable",
                "message": "Streaming token service is unavailable.",
            }
        },
    )


def token_issuance_success_response(data: TranscriptionTokenResponseData) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"data": data.model_dump(mode="json", exclude_none=False)},
    )
