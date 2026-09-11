from fastapi.responses import JSONResponse

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
