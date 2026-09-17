from app.services.intelligence.protocol import ExtractionResult


class FakeCaseIntelligenceService:
    def __init__(self, result: ExtractionResult | None = None) -> None:
        self._result = result or ExtractionResult()

    def set_result(self, result: ExtractionResult) -> None:
        self._result = result

    async def extract(self, case_text: str) -> ExtractionResult:
        return self._result
