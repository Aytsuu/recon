from typing import Any

from supabase import Client, create_client

from app.repositories.errors import RepositoryError
from app.schemas.case import CaseData
from app.schemas.clarification import ClarificationData
from app.schemas.draft import DraftData
from app.schemas.enums import (
    CaseStatus,
    ClarificationFieldKey,
    ClarificationStatus,
    InputMode,
)


def _row_to_clarification(row: dict[str, Any]) -> ClarificationData:
    return ClarificationData(
        id=int(row["id"]),
        field_key=ClarificationFieldKey(row["field_key"]),
        question=row["question"],
        answer=row.get("answer"),
        status=ClarificationStatus(row["status"]),
        position=int(row["position"]),
    )


def _row_to_draft(row: dict[str, Any]) -> DraftData:
    return DraftData(
        id=int(row["id"]),
        subject=row["subject"],
        body=row["body"],
        language_code=row.get("language_code"),
    )


def _row_to_case(row: dict[str, Any]) -> CaseData:
    clarifications_raw = row.get("case_clarification") or []
    draft_raw = row.get("support_draft")
    if isinstance(draft_raw, list):
        draft_row = draft_raw[0] if draft_raw else None
    else:
        draft_row = draft_raw

    clarifications = sorted(
        [_row_to_clarification(item) for item in clarifications_raw],
        key=lambda item: item.position,
    )
    draft = _row_to_draft(draft_row) if draft_row else None

    return CaseData(
        id=int(row["id"]),
        input_mode=InputMode(row["input_mode"]),
        status=CaseStatus(row["status"]),
        case_text=row.get("case_text"),
        language_code=row.get("language_code"),
        provider_name=row.get("provider_name"),
        service_name=row.get("service_name"),
        issue_category=row.get("issue_category"),
        problem_summary=row.get("problem_summary"),
        attempted_resolutions=list(row.get("attempted_resolutions") or []),
        desired_outcome=row.get("desired_outcome"),
        support_email=row.get("support_email"),
        support_phone=row.get("support_phone"),
        support_url=row.get("support_url"),
        clarifications=clarifications,
        draft=draft,
    )


def _case_select() -> str:
    return "*, case_clarification(*), support_draft(*)"


class SupabaseCaseRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    @classmethod
    def from_credentials(cls, url: str, service_role_key: str) -> "SupabaseCaseRepository":
        return cls(create_client(url, service_role_key))

    def _load_case_row(self, case_id: int) -> dict[str, Any] | None:
        try:
            response = (
                self._client.table("support_case")
                .select(_case_select())
                .eq("id", case_id)
                .maybe_single()
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("Failed to load case.") from exc

        if response is None or response.data is None:
            return None
        return response.data

    def create_case(
        self,
        *,
        input_mode: InputMode,
        status: CaseStatus,
        case_text: str | None = None,
        language_code: str | None = None,
        provider_name: str | None = None,
        service_name: str | None = None,
        issue_category: str | None = None,
        problem_summary: str | None = None,
        attempted_resolutions: list[str] | None = None,
        desired_outcome: str | None = None,
        support_email: str | None = None,
        support_phone: str | None = None,
        support_url: str | None = None,
    ) -> CaseData:
        payload = {
            "input_mode": input_mode.value,
            "status": status.value,
            "case_text": case_text,
            "language_code": language_code,
            "provider_name": provider_name,
            "service_name": service_name,
            "issue_category": issue_category,
            "problem_summary": problem_summary,
            "attempted_resolutions": list(attempted_resolutions or []),
            "desired_outcome": desired_outcome,
            "support_email": support_email,
            "support_phone": support_phone,
            "support_url": support_url,
        }
        try:
            response = self._client.table("support_case").insert(payload).execute()
        except Exception as exc:
            raise RepositoryError("Failed to create case.") from exc

        if not response.data:
            raise RepositoryError("Failed to create case.")
        row = response.data[0] if isinstance(response.data, list) else response.data
        row["case_clarification"] = []
        row["support_draft"] = None
        return _row_to_case(row)

    def get_case(self, case_id: int) -> CaseData | None:
        row = self._load_case_row(case_id)
        if row is None:
            return None
        return _row_to_case(row)

    def update_case(self, case_id: int, **fields: object) -> CaseData:
        allowed = {
            key: value
            for key, value in fields.items()
            if key not in {"id", "clarifications", "draft"}
        }
        if "input_mode" in allowed and isinstance(allowed["input_mode"], InputMode):
            allowed["input_mode"] = allowed["input_mode"].value
        if "status" in allowed and isinstance(allowed["status"], CaseStatus):
            allowed["status"] = allowed["status"].value

        if allowed:
            try:
                self._client.table("support_case").update(allowed).eq("id", case_id).execute()
            except Exception as exc:
                raise RepositoryError("Failed to update case.") from exc

        updated = self.get_case(case_id)
        if updated is None:
            raise RepositoryError(f"Case {case_id} not found after update.")
        return updated

    def create_or_update_clarification(
        self,
        case_id: int,
        clarification: ClarificationData,
    ) -> ClarificationData:
        payload = {
            "case_id": case_id,
            "field_key": clarification.field_key.value,
            "question": clarification.question,
            "answer": clarification.answer,
            "status": clarification.status.value,
            "position": clarification.position,
        }
        if clarification.id != 0:
            payload["id"] = clarification.id

        try:
            response = (
                self._client.table("case_clarification")
                .upsert(payload, on_conflict="case_id,field_key")
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("Failed to save clarification.") from exc

        if not response.data:
            raise RepositoryError("Failed to save clarification.")
        row = response.data[0] if isinstance(response.data, list) else response.data
        return _row_to_clarification(row)

    def list_clarifications(self, case_id: int) -> list[ClarificationData]:
        case = self.get_case(case_id)
        if case is None:
            raise RepositoryError(f"Case {case_id} not found.")
        return list(case.clarifications)

    def save_draft(self, case_id: int, draft: DraftData) -> DraftData:
        payload = {
            "case_id": case_id,
            "subject": draft.subject,
            "body": draft.body,
            "language_code": draft.language_code,
        }
        if draft.id != 0:
            payload["id"] = draft.id

        try:
            response = (
                self._client.table("support_draft").upsert(payload, on_conflict="case_id").execute()
            )
        except Exception as exc:
            raise RepositoryError("Failed to save draft.") from exc

        if not response.data:
            raise RepositoryError("Failed to save draft.")
        row = response.data[0] if isinstance(response.data, list) else response.data
        return _row_to_draft(row)

    def get_draft(self, case_id: int) -> DraftData | None:
        case = self.get_case(case_id)
        if case is None:
            return None
        return case.draft.model_copy(deep=True) if case.draft else None

    def delete_draft(self, case_id: int) -> None:
        try:
            self._client.table("support_draft").delete().eq("case_id", case_id).execute()
        except Exception as exc:
            raise RepositoryError("Failed to delete draft.") from exc

    def delete_case(self, case_id: int) -> None:
        try:
            self._client.table("support_case").delete().eq("id", case_id).execute()
        except Exception as exc:
            raise RepositoryError("Failed to delete case.") from exc
