from fastapi import APIRouter

from app.api.responses import not_implemented_response

router = APIRouter(tags=["extraction"])


@router.post("/cases/{case_id}/extract")
def extract_case(case_id: int):
    return not_implemented_response()
