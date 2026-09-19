from app.core.config import get_settings
from app.repositories.memory import InMemoryCaseRepository
from app.repositories.protocol import CaseRepository
from app.repositories.supabase import SupabaseCaseRepository
from app.services.draft import DraftService, LLMDraftService, TemplateDraftService
from app.services.intelligence import CaseIntelligenceService, RuleBasedCaseIntelligenceService
from app.services.intelligence.llm_based import LLMCaseIntelligenceService
from app.services.llm import GeminiLLMClient
from app.services.transcription import (
    AssemblyAIStreamingTokenService,
    FakeStreamingTokenService,
    StreamingTokenService,
)

_repository: CaseRepository | None = None


def get_case_repository() -> CaseRepository:
    global _repository
    if _repository is not None:
        return _repository

    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_role_key:
        _repository = SupabaseCaseRepository.from_credentials(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        return _repository

    _repository = InMemoryCaseRepository()
    return _repository


def reset_case_repository() -> CaseRepository:
    global _repository
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_role_key:
        _repository = SupabaseCaseRepository.from_credentials(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        return _repository

    _repository = InMemoryCaseRepository()
    return _repository


def get_streaming_token_service() -> StreamingTokenService:
    settings = get_settings()
    if settings.assemblyai_api_key:
        return AssemblyAIStreamingTokenService(api_key=settings.assemblyai_api_key)
    return FakeStreamingTokenService()


def _build_gemini_client() -> GeminiLLMClient:
    settings = get_settings()
    return GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


def get_case_intelligence_service() -> CaseIntelligenceService:
    settings = get_settings()
    if settings.gemini_api_key:
        return LLMCaseIntelligenceService(llm_client=_build_gemini_client())
    return RuleBasedCaseIntelligenceService()


def get_draft_service() -> DraftService:
    settings = get_settings()
    if settings.gemini_api_key:
        return LLMDraftService(llm_client=_build_gemini_client())
    return TemplateDraftService()
