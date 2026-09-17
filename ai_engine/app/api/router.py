from fastapi import APIRouter

from app.api.routes import (
    cases,
    clarifications,
    drafts,
    extraction,
    health,
    transcription,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(cases.router, prefix="/api")
api_router.include_router(transcription.router, prefix="/api")
api_router.include_router(extraction.router, prefix="/api")
api_router.include_router(clarifications.router, prefix="/api")
api_router.include_router(drafts.router, prefix="/api")
