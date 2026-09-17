from app.services.transcription.errors import TokenIssuanceFailedError
from app.services.transcription.protocol import StreamingTokenResult


class FakeStreamingTokenService:
    def __init__(
        self,
        *,
        token: str = "fake-streaming-token",
        should_fail: bool = False,
        failure_message: str = "Streaming token could not be issued.",
    ) -> None:
        self._token = token
        self._should_fail = should_fail
        self._failure_message = failure_message

    async def issue_token(self, expires_in_seconds: int = 60) -> StreamingTokenResult:
        if self._should_fail:
            raise TokenIssuanceFailedError(self._failure_message)
        return StreamingTokenResult(token=self._token, expires_in_seconds=expires_in_seconds)
