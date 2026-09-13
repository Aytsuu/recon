import json
from typing import Protocol

from app.schemas.case import CaseData
from app.schemas.draft import DraftData
from app.services.llm.protocol import LLMClient

DRAFT_SYSTEM_PROMPT = """You are a customer support complaint writer. Given structured case details,
write a formal but concise support complaint letter.
Return ONLY a JSON object with these exact keys:

{
  "subject": string (one line, e.g. "Internet connectivity complaint – Converge ICT"),
  "body": string (3 paragraphs max: state the problem, attempted fixes,
          desired outcome. Plain text, no markdown.)
}

Rules:
- Return only the JSON object. No explanation, no markdown fences.
- Address the letter to the provider's support team.
- Keep the body under 200 words."""


class DraftService(Protocol):
    async def compose(self, case: CaseData) -> DraftData: ...


def compose_draft(case: CaseData) -> DraftData:
    provider = case.provider_name or "the provider"
    problem = case.problem_summary or "the reported issue"
    outcome = case.desired_outcome or "a resolution"

    subject = f"Support complaint – {provider}"
    body = (
        f"Dear {provider} Support,\n\n"
        f"I am writing to report the following issue: {problem}\n\n"
        f"I would like the following outcome: {outcome}\n\n"
        "Thank you for your assistance."
    )

    return DraftData(
        id=0,
        subject=subject,
        body=body,
        language_code=case.language_code,
    )


class TemplateDraftService:
    async def compose(self, case: CaseData) -> DraftData:
        return compose_draft(case)


def _format_draft_prompt(case: CaseData) -> str:
    attempted = ", ".join(case.attempted_resolutions) if case.attempted_resolutions else "None"
    return (
        f"Provider: {case.provider_name or 'Unknown'}\n"
        f"Service: {case.service_name or 'Unknown'}\n"
        f"Issue category: {case.issue_category or 'Unknown'}\n"
        f"Problem summary: {case.problem_summary or case.case_text or 'Unknown'}\n"
        f"Attempted resolutions: {attempted}\n"
        f"Desired outcome: {case.desired_outcome or 'Unknown'}"
    )


def _parse_draft_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise json.JSONDecodeError("Expected JSON object.", cleaned, 0)
    return payload


class LLMDraftService:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def compose(self, case: CaseData) -> DraftData:
        try:
            raw = await self._llm_client.complete(
                DRAFT_SYSTEM_PROMPT,
                _format_draft_prompt(case),
            )
            payload = _parse_draft_json(raw)
            subject = str(payload.get("subject", "")).strip()
            body = str(payload.get("body", "")).strip()
            if not subject or not body:
                raise json.JSONDecodeError("Missing subject or body.", raw, 0)
            return DraftData(
                id=0,
                subject=subject,
                body=body,
                language_code=case.language_code,
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return compose_draft(case)
