from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.api.responses import not_implemented_response

router = APIRouter(tags=["transcription"])


@router.post("/cases/{case_id}/transcribe")
def transcribe_case(case_id: int, audio: Annotated[UploadFile, File()]):
    return not_implemented_response()
