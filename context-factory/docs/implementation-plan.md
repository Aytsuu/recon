# RECON Parallel Implementation Plan

This document coordinates two parallel feature tracks. Detailed work is split
into [Person A: AI Engine](../implementations/ai-engine-implementation-plan.md) and
[Person B: Web and Supabase](../implementations/web-supabase-implementation-plan.md).

## Goal

Build one local feature loop:

```text
Typed or voice problem
  -> reviewed case text
  -> extracted support details
  -> focused clarification
  -> editable support draft
  -> user copies the draft
```

The MVP does not send an email, submit a ticket, or promise a verified provider
route.

## Ownership

| Owner | Exclusive files and responsibilities |
| --- | --- |
| **Person A - AI Engine** | `ai_engine/`: FastAPI routes, API schemas, AssemblyAI adapter, case extraction, clarification rules, draft generation, API tests, and server-side Supabase repository. |
| **Person B - Web and Supabase** | `apps/web/`: Astro screens, recorder, API client, UI states, browser tests. `supabase/`: the feature migration, seed fixtures, and local database verification. |
| **Shared** | This contract, API fixture examples, and integration checkpoints. Neither person changes the other owner's directory without coordination. |

## Shared feature contract

Use snake_case JSON field names so FastAPI models, database columns, and the
web client agree without a mapping layer.

### Case response envelope

Every successful case endpoint returns one stable envelope:

```json
{
  "data": {
    "id": 1,
    "input_mode": "typed",
    "status": "input_ready",
    "case_text": "My internet keeps disconnecting.",
    "language_code": "en",
    "provider_name": "Converge ICT",
    "service_name": "Residential fiber internet",
    "issue_category": "internet_connectivity",
    "problem_summary": "Intermittent internet connection.",
    "attempted_resolutions": ["Restarted the router"],
    "desired_outcome": "Restore stable service",
    "clarifications": [],
    "draft": null
  }
}
```

`clarifications` contains `id`, `field_key`, `question`, `answer`, `status`,
and `position`. `draft` is either `null` or contains `id`, `subject`, `body`,
and `language_code`.

### Initial endpoints

| Method and route | Request purpose | Response |
| --- | --- | --- |
| `POST /api/cases` | Create a typed case or an empty voice case. | Complete case payload. |
| `GET /api/cases/{case_id}` | Load the current case, questions, and draft. | Complete case payload. |
| `PATCH /api/cases/{case_id}` | Save reviewed case text or edited structured fields. | Updated case payload. |
| `POST /api/cases/{case_id}/transcribe` | Upload voice audio for the MVP transcription flow. | A `data` envelope containing `case_id`, `transcript`, and optional `language_code` for user review; it does not persist the transcript. |
| `POST /api/cases/{case_id}/extract` | Populate structured details and pending clarifications. | Updated case payload. |
| `PATCH /api/cases/{case_id}/clarifications/{clarification_id}` | Save an answer or mark a question skipped. | Updated case payload. |
| `POST /api/cases/{case_id}/draft` | Generate the current support draft. | Updated case payload with `draft`. |
| `PATCH /api/cases/{case_id}/draft` | Save user edits to subject or body. | Updated case payload with `draft`. |

### State and invalidation rules

- Typed cases start as `input_ready`; voice cases start as `transcribing`.
- After the user reviews a voice transcript, the web app sends it through
  `PATCH /api/cases/{case_id}`. Person A then saves it as `case_text` and
  changes the case to `input_ready`.
- Extraction produces either `clarifying` with pending questions or
  `ready_for_draft` when no required field is missing.
- Draft generation changes the case to `draft_ready`.
- A material change to `case_text`, provider, summary, or desired outcome
  removes the current draft and moves the case back to `input_ready` or
  `ready_for_draft`.
- The feature ends with the user copying the draft; no API performs an external
  contact action.
- Any contract change requires agreement from both owners and an update to this
  document and the shared fixtures before implementation continues.

## Parallel execution order

1. Agree on the contract above and add shared JSON fixtures before either track
   builds UI or persistence behavior around it.
2. **Person A** implements every endpoint against an in-memory repository and
   mocked external services. **Person B** implements the Astro flow with the
   same fixture data and API-client mock.
3. **Person B** creates and verifies the Supabase migration. **Person A** then
   replaces the in-memory repository with the Supabase repository without
   changing endpoint shapes.
4. **Person B** switches the web API client from fixtures to the local FastAPI
   server. Both owners run the integration checklist below.

## Integration checkpoints

- [ ] **Complete:** Agree on a checked-in fixture for an empty typed case, a
  voice-transcribing case, a case with one clarification, and a draft-ready
  case.
  - [ ] **Verify:** Person A's API-schema tests and Person B's API-client tests
    both consume the same fixtures without field translation.

- [ ] **Complete:** Connect Person A's repository to Person B's migration.
  - [ ] **Verify:** `supabase db reset` followed by API tests can create, load,
    update, clarify, draft, edit, and delete one case.

- [ ] **Complete:** Connect the Astro API client to the running FastAPI server.
  - [ ] **Verify:** A typed case completes the full loop in the browser; the
    voice case completes the same loop with a mocked AssemblyAI response.

- [ ] **Complete:** Run one real AssemblyAI transcription through the connected
  local flow after the mocked path passes.
  - [ ] **Verify:** The user can correct the result, generate a draft, and copy
    it without a manually edited database row.

## Deferred work

Authentication, user-specific RLS policies, retention rules, provider-route
governance, external sending, queues, production deployment, and operations
remain out of this parallel feature scope.
