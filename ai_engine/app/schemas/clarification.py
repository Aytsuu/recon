from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ClarificationFieldKey, ClarificationStatus


class ClarificationData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    field_key: ClarificationFieldKey
    question: str
    answer: str | None = None
    status: ClarificationStatus
    position: int = Field(gt=0)
