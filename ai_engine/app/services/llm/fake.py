class FakeLLMClient:
    def __init__(self, response: str = "{}") -> None:
        self.response = response

    async def complete(self, system: str, prompt: str) -> str:
        return self.response
