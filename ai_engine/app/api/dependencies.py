from app.core.config import get_settings
from app.repositories.memory import InMemoryCaseRepository
from app.services.draft import DraftService, LLMDraftService, TemplateDraftService
from app.services.intelligence import CaseIntelligenceService, RuleBasedCaseIntelligenceService
from app.services.intelligence.llm_based import LLMCaseIntelligenceService
from app.services.llm import OpenAILLMClient
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


def _build_openai_client() -> OpenAILLMClient:
    settings = get_settings()
    return OpenAILLMClient(api_key=settings.openai_api_key, model=settings.openai_model)


def get_case_intelligence_service() -> CaseIntelligenceService:
    settings = get_settings()
    if settings.openai_api_key:
        return LLMCaseIntelligenceService(llm_client=_build_openai_client())
    return RuleBasedCaseIntelligenceService()


def get_draft_service() -> DraftService:
    settings = get_settings()
    if settings.openai_api_key:
        return LLMDraftService(llm_client=_build_openai_client())
    return TemplateDraftService()
