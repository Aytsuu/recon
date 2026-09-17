from app.schemas.enums import ClarificationFieldKey

CLARIFICATION_QUESTIONS: dict[ClarificationFieldKey, str] = {
    ClarificationFieldKey.provider_name: "Which provider or company are you contacting?",
    ClarificationFieldKey.problem_summary: "Can you briefly summarize the problem?",
    ClarificationFieldKey.desired_outcome: "What outcome would you like from support?",
}
