import httpx

from app.services.transcription.errors import TokenIssuanceFailedError, TokenServiceUnavailableError
from app.services.transcription.protocol import StreamingTokenResult

ASSEMBLYAI_STREAMING_BASE_URL = "https://streaming.assemblyai.com"


class AssemblyAIStreamingTokenService:
    def __init__(
        self,
        api_key: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client

    async def issue_token(self, expires_in_seconds: int = 60) -> StreamingTokenResult:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            base_url=ASSEMBLYAI_STREAMING_BASE_URL,
            headers={"authorization": self._api_key},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        try:
            response = await client.get(
                "/v3/token",
                params={"expires_in_seconds": expires_in_seconds},
            )
            response.raise_for_status()
            token = response.json().get("token")
            if not token or not str(token).strip():
                raise TokenIssuanceFailedError()
            return StreamingTokenResult(token=str(token), expires_in_seconds=expires_in_seconds)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as exc:
            raise TokenServiceUnavailableError() from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                raise TokenServiceUnavailableError() from exc
            raise TokenIssuanceFailedError() from exc
        finally:
            if owns_client:
                await client.aclose()
