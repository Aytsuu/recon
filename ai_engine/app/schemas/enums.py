from enum import StrEnum


class InputMode(StrEnum):
    typed = "typed"
    voice = "voice"


class CaseStatus(StrEnum):
    transcribing = "transcribing"
    input_ready = "input_ready"
    clarifying = "clarifying"
    ready_for_draft = "ready_for_draft"
    draft_ready = "draft_ready"
    failed = "failed"


class ClarificationStatus(StrEnum):
    pending = "pending"
    answered = "answered"
    skipped = "skipped"


class ClarificationFieldKey(StrEnum):
    provider_name = "provider_name"
    problem_summary = "problem_summary"
    desired_outcome = "desired_outcome"
