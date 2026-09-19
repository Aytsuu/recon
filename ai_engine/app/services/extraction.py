from app.repositories.protocol import CaseRepository
from app.schemas.case import CaseData
from app.schemas.clarification import ClarificationData
from app.schemas.enums import CaseStatus, ClarificationStatus
from app.services.intelligence.protocol import ExtractionResult
from app.services.intelligence.questions import CLARIFICATION_QUESTIONS
from app.services.providers import lookup as provider_lookup


def apply_extraction(
    case: CaseData,
    result: ExtractionResult,
    repository: CaseRepository,
) -> CaseData:
    repository.update_case(
        case.id,
        provider_name=result.provider_name,
        service_name=result.service_name,
        issue_category=result.issue_category,
        problem_summary=result.problem_summary,
        attempted_resolutions=list(result.attempted_resolutions),
        desired_outcome=result.desired_outcome,
    )

    contact = provider_lookup(result.provider_name)
    if contact is not None:
        repository.update_case(
            case.id,
            support_email=contact.support_email,
            support_phone=contact.support_phone,
            support_url=contact.support_url,
        )

    existing_keys = {item.field_key for item in case.clarifications}
    next_position = max((item.position for item in case.clarifications), default=0)

    for field_key in result.missing_fields:
        if field_key in existing_keys:
            continue
        next_position += 1
        repository.create_or_update_clarification(
            case.id,
            ClarificationData(
                id=0,
                field_key=field_key,
                question=CLARIFICATION_QUESTIONS[field_key],
                status=ClarificationStatus.pending,
                position=next_position,
            ),
        )

    status = CaseStatus.clarifying if result.missing_fields else CaseStatus.ready_for_draft
    updated = repository.get_case(case.id)
    if updated is None:
        raise ValueError(f"Case {case.id} not found after extraction")
    return repository.update_case(case.id, status=status)
