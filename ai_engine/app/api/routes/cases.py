from fastapi import APIRouter

from app.api.responses import not_implemented_response
from app.schemas.requests import CreateCaseRequest, UpdateCaseRequest

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("")
def create_case(_payload: CreateCaseRequest):
    return not_implemented_response()


@router.get("/{case_id}")
def get_case(case_id: int):
    return not_implemented_response()


@router.patch("/{case_id}")
def update_case(case_id: int, _payload: UpdateCaseRequest):
    return not_implemented_response()
