from typing import Protocol


class LLMClient(Protocol):
    async def complete(self, system: str, prompt: str) -> str: ...
