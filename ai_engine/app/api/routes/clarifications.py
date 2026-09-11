from fastapi import APIRouter

from app.api.responses import not_implemented_response
from app.schemas.requests import UpdateClarificationRequest

router = APIRouter(tags=["clarifications"])


@router.patch("/cases/{case_id}/clarifications/{clarification_id}")
def update_clarification(
    case_id: int,
    clarification_id: int,
    _payload: UpdateClarificationRequest,
):
    return not_implemented_response()
