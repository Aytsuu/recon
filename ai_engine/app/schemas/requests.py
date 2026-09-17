from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.enums import ClarificationStatus, InputMode


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


class CreateCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_mode: InputMode
    case_text: str | None = None
    language_code: str | None = None
    provider_name: str | None = None

    @model_validator(mode="after")
    def validate_case_text(self) -> Self:
        if self.input_mode == InputMode.typed and _is_blank(self.case_text):
            raise ValueError("case_text is required for typed cases and cannot be blank")
        return self


class UpdateCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_text: str | None = None
    language_code: str | None = None
    provider_name: str | None = None
    service_name: str | None = None
    issue_category: str | None = None
    problem_summary: str | None = None
    attempted_resolutions: list[str] | None = None
    desired_outcome: str | None = None

    @model_validator(mode="after")
    def validate_case_text(self) -> Self:
        if self.case_text is not None and self.case_text.strip() == "":
            raise ValueError("case_text cannot be blank")
        return self


class UpdateClarificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ClarificationStatus
    answer: str | None = None

    @model_validator(mode="after")
    def validate_answer_rules(self) -> Self:
        if self.status == ClarificationStatus.answered and _is_blank(self.answer):
            raise ValueError("answer is required when status is answered")
        elif (
            self.status in {ClarificationStatus.pending, ClarificationStatus.skipped}
            and self.answer is not None
            and self.answer.strip() != ""
        ):
            raise ValueError("answer must not be provided for pending or skipped status")
        return self


class UpdateDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str | None = None
    body: str | None = None
    language_code: str | None = None

    @model_validator(mode="after")
    def validate_draft_fields(self) -> Self:
        if self.subject is not None and self.subject.strip() == "":
            raise ValueError("subject cannot be blank")
        if self.body is not None and self.body.strip() == "":
            raise ValueError("body cannot be blank")
        return self
