from typing import Protocol

from app.schemas.case import CaseData
from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import CaseStatus, InputMode


class CaseRepository(Protocol):
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
    ) -> CaseData: ...

    def get_case(self, case_id: int) -> CaseData | None: ...

    def update_case(self, case_id: int, **fields: object) -> CaseData: ...

    def create_or_update_clarification(
        self,
        case_id: int,
        clarification: ClarificationData,
    ) -> ClarificationData: ...

    def list_clarifications(self, case_id: int) -> list[ClarificationData]: ...

    def save_draft(self, case_id: int, draft: DraftData) -> DraftData: ...

    def get_draft(self, case_id: int) -> DraftData | None: ...

    def delete_draft(self, case_id: int) -> None: ...

    def delete_case(self, case_id: int) -> None: ...
