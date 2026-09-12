from app.schemas.case import CaseData
from app.schemas.clarification import ClarificationData
from app.schemas.enums import CaseStatus, ClarificationFieldKey, ClarificationStatus, InputMode

REQUIRED_FIELDS = ("provider_name", "problem_summary", "desired_outcome")

MATERIAL_FIELDS = frozenset(
    {
        "case_text",
        "provider_name",
        "service_name",
        "issue_category",
        "problem_summary",
        "attempted_resolutions",
        "desired_outcome",
    }
)

CLARIFICATION_FIELD_MAP: dict[ClarificationFieldKey, str] = {
    ClarificationFieldKey.provider_name: "provider_name",
    ClarificationFieldKey.problem_summary: "problem_summary",
    ClarificationFieldKey.desired_outcome: "desired_outcome",
}


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def has_required_fields(case: CaseData) -> bool:
    return all(not _is_blank(getattr(case, field)) for field in REQUIRED_FIELDS)


def has_pending_clarifications(case: CaseData) -> bool:
    return any(
        clarification.status == ClarificationStatus.pending for clarification in case.clarifications
    )


def resolve_case_status(case: CaseData) -> CaseStatus:
    if has_pending_clarifications(case):
        return CaseStatus.clarifying
    if has_required_fields(case):
        return CaseStatus.ready_for_draft
    return CaseStatus.input_ready


def is_material_field(field_name: str) -> bool:
    return field_name in MATERIAL_FIELDS


def apply_case_patch(case: CaseData, updates: dict[str, object]) -> CaseData:
    working_updates = dict(updates)

    if (
        "case_text" in working_updates
        and case.input_mode == InputMode.voice
        and case.status == CaseStatus.transcribing
        and not _is_blank(working_updates["case_text"])
    ):
        working_updates["status"] = CaseStatus.input_ready

    draft_invalidated = False
    if case.draft is not None:
        for field_name, new_value in working_updates.items():
            if is_material_field(field_name) and new_value != getattr(case, field_name):
                draft_invalidated = True
                break

    if draft_invalidated:
        working_updates["draft"] = None

    patched = case.model_copy(update=working_updates, deep=True)

    if draft_invalidated:
        patched = patched.model_copy(update={"status": resolve_case_status(patched)}, deep=True)

    return patched


def apply_clarification_update(
    case: CaseData,
    clarification: ClarificationData,
    payload_status: ClarificationStatus,
    answer: str | None,
) -> CaseData:
    updated_clarifications: list[ClarificationData] = []
    case_updates: dict[str, object] = {}

    for item in case.clarifications:
        if item.id != clarification.id:
            updated_clarifications.append(item.model_copy(deep=True))
            continue

        updated_item = item.model_copy(
            update={
                "status": payload_status,
                "answer": answer if payload_status == ClarificationStatus.answered else None,
            },
            deep=True,
        )
        updated_clarifications.append(updated_item)

        if payload_status == ClarificationStatus.answered and answer is not None:
            case_field = CLARIFICATION_FIELD_MAP[item.field_key]
            case_updates[case_field] = answer.strip()

    interim_case = case.model_copy(
        update={**case_updates, "clarifications": updated_clarifications},
        deep=True,
    )
    return interim_case.model_copy(update={"status": resolve_case_status(interim_case)}, deep=True)
