from app.schemas.enums import ClarificationFieldKey
from app.services.intelligence.protocol import ExtractionResult

REQUIRED_FIELD_KEYS = (
    ClarificationFieldKey.provider_name,
    ClarificationFieldKey.problem_summary,
    ClarificationFieldKey.desired_outcome,
)


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _missing_fields(
    provider_name: str | None,
    problem_summary: str | None,
    desired_outcome: str | None,
) -> tuple[ClarificationFieldKey, ...]:
    values = {
        ClarificationFieldKey.provider_name: provider_name,
        ClarificationFieldKey.problem_summary: problem_summary,
        ClarificationFieldKey.desired_outcome: desired_outcome,
    }
    return tuple(field_key for field_key in REQUIRED_FIELD_KEYS if _is_blank(values[field_key]))


class RuleBasedCaseIntelligenceService:
    async def extract(self, case_text: str) -> ExtractionResult:
        text = case_text.strip()
        lower = text.lower()

        provider_name = "Converge ICT" if "converge" in lower else None

        service_name = None
        issue_category = None
        if any(keyword in lower for keyword in ("internet", "connection", "fiber", "los")):
            service_name = "Residential fiber internet"
            issue_category = "internet_connectivity"

        problem_summary = text if len(text) <= 200 else f"{text[:197]}..."

        attempted_resolutions: list[str] = []
        if "restart" in lower:
            attempted_resolutions.append("Restarted the router")

        desired_outcome = None
        if any(keyword in lower for keyword in ("restore", "stable", "fix", "resolved")):
            desired_outcome = "Restore stable service"

        missing_fields = _missing_fields(provider_name, problem_summary, desired_outcome)

        return ExtractionResult(
            provider_name=provider_name,
            service_name=service_name,
            issue_category=issue_category,
            problem_summary=problem_summary,
            attempted_resolutions=tuple(attempted_resolutions),
            desired_outcome=desired_outcome,
            missing_fields=missing_fields,
        )
