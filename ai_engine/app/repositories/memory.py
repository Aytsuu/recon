from app.schemas.case import CaseData
from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import CaseStatus, InputMode


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._cases: dict[int, CaseData] = {}
        self._next_case_id = 1
        self._next_clarification_id = 1
        self._next_draft_id = 1

    def create_case(
        self,
        *,
        input_mode: InputMode,
        status: CaseStatus,
        case_text: str | None = None,
        language_code: str | None = None,
        provider_name: str | None = None,
        service_name: str | None = None,
        issue_category: str | None = None,
        problem_summary: str | None = None,
        attempted_resolutions: list[str] | None = None,
        desired_outcome: str | None = None,
        support_email: str | None = None,
        support_phone: str | None = None,
        support_url: str | None = None,
    ) -> CaseData:
        case = CaseData(
            id=self._next_case_id,
            input_mode=input_mode,
            status=status,
            case_text=case_text,
            language_code=language_code,
            provider_name=provider_name,
            service_name=service_name,
            issue_category=issue_category,
            problem_summary=problem_summary,
            attempted_resolutions=list(attempted_resolutions or []),
            desired_outcome=desired_outcome,
            support_email=support_email,
            support_phone=support_phone,
            support_url=support_url,
        )
        self._cases[case.id] = case
        self._next_case_id += 1
        return case.model_copy(deep=True)

    def get_case(self, case_id: int) -> CaseData | None:
        case = self._cases.get(case_id)
        if case is None:
            return None
        return case.model_copy(deep=True)

    def update_case(self, case_id: int, **fields: object) -> CaseData:
        case = self._cases[case_id]
        updated = case.model_copy(update=fields, deep=True)
        self._cases[case_id] = updated
        return updated.model_copy(deep=True)

    def create_or_update_clarification(
        self,
        case_id: int,
        clarification: ClarificationData,
    ) -> ClarificationData:
        case = self._cases[case_id]
        clarifications = list(case.clarifications)
        stored = clarification.model_copy(deep=True)

        if stored.id == 0:
            stored = stored.model_copy(update={"id": self._next_clarification_id})
            self._next_clarification_id += 1
            clarifications.append(stored)
        else:
            clarifications = [stored if item.id == stored.id else item for item in clarifications]
            if not any(item.id == stored.id for item in clarifications):
                clarifications.append(stored)

        clarifications.sort(key=lambda item: item.position)
        self._cases[case_id] = case.model_copy(update={"clarifications": clarifications}, deep=True)
        return stored.model_copy(deep=True)

    def list_clarifications(self, case_id: int) -> list[ClarificationData]:
        case = self._cases[case_id]
        return [item.model_copy(deep=True) for item in case.clarifications]

    def save_draft(self, case_id: int, draft: DraftData) -> DraftData:
        case = self._cases[case_id]
        stored = draft.model_copy(deep=True)
        if stored.id == 0:
            stored = stored.model_copy(update={"id": self._next_draft_id})
            self._next_draft_id += 1
        self._cases[case_id] = case.model_copy(update={"draft": stored}, deep=True)
        return stored.model_copy(deep=True)

    def get_draft(self, case_id: int) -> DraftData | None:
        case = self._cases.get(case_id)
        if case is None or case.draft is None:
            return None
        return case.draft.model_copy(deep=True)

    def delete_draft(self, case_id: int) -> None:
        case = self._cases[case_id]
        self._cases[case_id] = case.model_copy(update={"draft": None}, deep=True)

    def delete_case(self, case_id: int) -> None:
        del self._cases[case_id]
