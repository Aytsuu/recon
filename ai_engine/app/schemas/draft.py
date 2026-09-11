from pydantic import BaseModel, ConfigDict


class DraftData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    subject: str
    body: str
    language_code: str | None = None
