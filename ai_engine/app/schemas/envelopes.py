from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from app.schemas.case import CaseData

DataT = TypeVar("DataT")


class SuccessEnvelope(BaseModel, Generic[DataT]):
    model_config = ConfigDict(extra="forbid")

    data: DataT


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


CaseResponse = SuccessEnvelope[CaseData]

NOT_IMPLEMENTED_CODE = "not_implemented"
NOT_IMPLEMENTED_MESSAGE = "This endpoint is reserved for a later implementation phase."
