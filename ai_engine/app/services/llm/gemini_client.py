import httpx

from app.services.llm.errors import LLMCompletionError

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiLLMClient:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-1.5-flash",
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client
        self._timeout_seconds = timeout_seconds

    def _build_url(self) -> str:
        return f"{GEMINI_API_BASE_URL}/{self._model}:generateContent"

    async def complete(self, system: str, prompt: str) -> str:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout_seconds, connect=10.0),
        )
        try:
            response = await client.post(
                self._build_url(),
                params={"key": self._api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                },
            )
            response.raise_for_status()
            payload = response.json()
            candidates = payload.get("candidates") or []
            if not candidates:
                raise LLMCompletionError("LLM response did not include candidates.")
            content = candidates[0].get("content", {})
            parts = content.get("parts") or []
            if not parts:
                raise LLMCompletionError("LLM response did not include content parts.")
            text = parts[0].get("text")
            if not isinstance(text, str) or not text.strip():
                raise LLMCompletionError("LLM response did not include text content.")
            return text
        except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as exc:
            raise LLMCompletionError("LLM transport failed.") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMCompletionError("LLM completion request failed.") from exc
        finally:
            if owns_client:
                await client.aclose()
