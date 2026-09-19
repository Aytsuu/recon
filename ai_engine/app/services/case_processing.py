from app.repositories.protocol import CaseRepository
from app.schemas.case import CaseData
from app.schemas.enums import CaseStatus
from app.services.draft import DraftService
from app.services.extraction import apply_extraction
from app.services.intelligence.protocol import CaseIntelligenceService


async def process_case_intelligence(
    case: CaseData,
    repository: CaseRepository,
    intelligence_service: CaseIntelligenceService,
    draft_service: DraftService,
) -> CaseData:
    if case.case_text is None or case.case_text.strip() == "":
        raise ValueError("case_text is required for intelligence processing.")

    result = await intelligence_service.extract(case.case_text)
    updated = apply_extraction(case, result, repository)

    refreshed = repository.get_case(case.id)
    if refreshed is None:
        raise ValueError(f"Case {case.id} not found after extraction.")

    draft = await draft_service.compose(refreshed)
    repository.save_draft(case.id, draft)

    if updated.status == CaseStatus.clarifying:
        return repository.get_case(case.id) or updated

    final = repository.update_case(case.id, status=CaseStatus.draft_ready)
    return final
