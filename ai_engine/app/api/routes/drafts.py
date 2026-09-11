from fastapi import APIRouter

from app.api.responses import not_implemented_response
from app.schemas.requests import UpdateDraftRequest

router = APIRouter(tags=["drafts"])


@router.post("/cases/{case_id}/draft")
def generate_draft(case_id: int):
    return not_implemented_response()


@router.patch("/cases/{case_id}/draft")
def update_draft(case_id: int, _payload: UpdateDraftRequest):
    return not_implemented_response()
