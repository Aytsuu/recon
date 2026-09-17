from dataclasses import dataclass
from typing import Protocol

from app.schemas.enums import ClarificationFieldKey


@dataclass(frozen=True)
class ExtractionResult:
    provider_name: str | None = None
    service_name: str | None = None
    issue_category: str | None = None
    problem_summary: str | None = None
    attempted_resolutions: tuple[str, ...] = ()
    desired_outcome: str | None = None
    missing_fields: tuple[ClarificationFieldKey, ...] = ()


class CaseIntelligenceService(Protocol):
    async def extract(self, case_text: str) -> ExtractionResult: ...
