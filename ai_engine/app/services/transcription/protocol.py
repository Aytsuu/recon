from dataclasses import dataclass
from typing import Protocol

STREAMING_WS_URL = "wss://streaming.assemblyai.com/v3/ws"
DEFAULT_TOKEN_EXPIRES_IN_SECONDS = 60


@dataclass(frozen=True)
class StreamingTokenResult:
    token: str
    expires_in_seconds: int


class StreamingTokenService(Protocol):
    async def issue_token(
        self, expires_in_seconds: int = DEFAULT_TOKEN_EXPIRES_IN_SECONDS
    ) -> StreamingTokenResult: ...
