import httpx

from app.services.llm.errors import LLMCompletionError

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


class OpenAILLMClient:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def complete(self, system: str, prompt: str) -> str:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout_seconds, connect=10.0),
        )
        try:
            response = await client.post(
                OPENAI_CHAT_COMPLETIONS_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
            choices = payload.get("choices") or []
            if not choices:
                raise LLMCompletionError("LLM response did not include choices.")
            content = choices[0].get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                raise LLMCompletionError("LLM response did not include message content.")
            return content
        except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as exc:
            raise LLMCompletionError("LLM transport failed.") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMCompletionError("LLM completion request failed.") from exc
        finally:
            if owns_client:
                await client.aclose()
