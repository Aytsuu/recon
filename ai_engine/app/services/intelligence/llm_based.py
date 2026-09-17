import json

from app.schemas.enums import ClarificationFieldKey
from app.services.intelligence.protocol import ExtractionResult
from app.services.intelligence.rule_based import _missing_fields
from app.services.llm.protocol import LLMClient

EXTRACTION_SYSTEM_PROMPT = """You are a support case analyst. Given a customer's problem description,
extract structured fields and return ONLY a JSON object with these exact keys:

{
  "provider_name": string or null,
  "service_name": string or null,
  "issue_category": string or null,
  "problem_summary": string (concise one-sentence summary) or null,
  "attempted_resolutions": array of strings (empty if none),
  "desired_outcome": string (what the customer wants) or null
}

Rules:
- Return only the JSON object. No explanation, no markdown fences.
- "issue_category" must be a short snake_case identifier, e.g. "internet_connectivity".
- If a field cannot be determined from the text, use null.
- "desired_outcome" is what the customer explicitly or implicitly wants resolved."""

ALL_MISSING_FIELDS = (
    ClarificationFieldKey.provider_name,
    ClarificationFieldKey.problem_summary,
    ClarificationFieldKey.desired_outcome,
)


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise json.JSONDecodeError("Expected JSON object.", cleaned, 0)
    return payload


def _fallback_extraction_result() -> ExtractionResult:
    return ExtractionResult(missing_fields=ALL_MISSING_FIELDS)


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value).strip() or None


def _coerce_attempted_resolutions(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


class LLMCaseIntelligenceService:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def extract(self, case_text: str) -> ExtractionResult:
        try:
            raw = await self._llm_client.complete(
                EXTRACTION_SYSTEM_PROMPT,
                case_text.strip(),
            )
            payload = _parse_json_object(raw)
        except (json.JSONDecodeError, TypeError):
            return _fallback_extraction_result()

        provider_name = _coerce_optional_str(payload.get("provider_name"))
        service_name = _coerce_optional_str(payload.get("service_name"))
        issue_category = _coerce_optional_str(payload.get("issue_category"))
        problem_summary = _coerce_optional_str(payload.get("problem_summary"))
        desired_outcome = _coerce_optional_str(payload.get("desired_outcome"))
        attempted_resolutions = _coerce_attempted_resolutions(payload.get("attempted_resolutions"))

        return ExtractionResult(
            provider_name=provider_name,
            service_name=service_name,
            issue_category=issue_category,
            problem_summary=problem_summary,
            attempted_resolutions=attempted_resolutions,
            desired_outcome=desired_outcome,
            missing_fields=_missing_fields(provider_name, problem_summary, desired_outcome),
        )
