from app.core.config import get_settings
from app.repositories.memory import InMemoryCaseRepository
from app.services.intelligence import CaseIntelligenceService, RuleBasedCaseIntelligenceService
from app.services.transcription import (
    AssemblyAIStreamingTokenService,
    FakeStreamingTokenService,
    StreamingTokenService,
)

_repository: InMemoryCaseRepository | None = None


def get_case_repository() -> InMemoryCaseRepository:
    global _repository
    if _repository is None:
        _repository = InMemoryCaseRepository()
    return _repository


def reset_case_repository() -> InMemoryCaseRepository:
    global _repository
    _repository = InMemoryCaseRepository()
    return _repository


def get_streaming_token_service() -> StreamingTokenService:
    settings = get_settings()
    if settings.assemblyai_api_key:
        return AssemblyAIStreamingTokenService(api_key=settings.assemblyai_api_key)
    return FakeStreamingTokenService()


def get_case_intelligence_service() -> CaseIntelligenceService:
    return RuleBasedCaseIntelligenceService()
