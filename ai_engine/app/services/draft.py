from app.schemas.case import CaseData
from app.schemas.draft import DraftData


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
