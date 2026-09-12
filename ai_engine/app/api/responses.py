from fastapi.responses import JSONResponse

from app.schemas.case import CaseData
from app.schemas.envelopes import NOT_IMPLEMENTED_CODE, NOT_IMPLEMENTED_MESSAGE


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
