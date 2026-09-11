from pydantic import BaseModel, ConfigDict, Field

from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import CaseStatus, InputMode


class CaseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    input_mode: InputMode
    status: CaseStatus
    case_text: str | None = None
    language_code: str | None = None
    provider_name: str | None = None
    service_name: str | None = None
    issue_category: str | None = None
    problem_summary: str | None = None
    attempted_resolutions: list[str] = Field(default_factory=list)
    desired_outcome: str | None = None
    clarifications: list[ClarificationData] = Field(default_factory=list)
    draft: DraftData | None = None
