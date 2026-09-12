from pydantic import BaseModel, ConfigDict

from app.services.transcription.protocol import STREAMING_WS_URL


class TranscriptionTokenResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: int
    token: str
    expires_in_seconds: int
    ws_url: str = STREAMING_WS_URL
