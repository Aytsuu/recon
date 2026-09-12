# Person A Plan: AI Engine

**Owner:** Person A  
**Workspace:** `ai_engine/` only  
**Shared contract:** [Parallel Implementation Plan](../docs/implementation-plan.md)

## Responsibility

Person A owns the FastAPI service that turns case input into a structured case,
focused questions, and an editable draft. This track must keep the endpoint and
JSON contract in the shared plan stable.

Person A does not edit `apps/web/` or author Supabase migration SQL. Person B
owns those areas.

## Build sequence

### A1. Establish the API contract and test seam

- [x] **Complete:** Add Pydantic request and response models matching the shared
  `Case` payload, clarification payload, draft payload, and endpoint requests.
  - [x] **Verify:** API-schema tests accept the shared JSON fixtures and reject
    malformed state, blank typed input, and invalid clarification answers.

- [x] **Complete:** Add route modules for cases, transcription, extraction,
  clarifications, and drafts under `ai_engine/app/api/routes/`.
  - [x] **Verify:** Each route is registered under `/api`, returns the agreed
    response shape, and leaves `GET /health` unchanged.

- [x] **Complete:** Define a small `CaseRepository` interface for create, load,
  update, clarification, draft, and delete operations.
  - [x] **Verify:** Repository contract tests pass against an in-memory
    implementation before the Supabase-backed implementation exists.

### A2. Implement the case state machine

- [x] **Complete:** Implement typed case creation as `input_ready` and empty
  voice case creation as `transcribing`.
  - [x] **Verify:** API tests prove the two creation modes return the expected
    state and reject invalid combinations of mode, status, and `case_text`.

- [x] **Complete:** Implement case updates for reviewed `case_text`, provider,
  service, category, summary, attempted resolutions, and desired outcome.
  - [x] **Verify:** A material edit removes the existing draft and returns a
    case to `input_ready` or `ready_for_draft` as required by the shared plan.

- [x] **Complete:** Implement clarification answers and skipped questions.
  - [x] **Verify:** A case cannot become `ready_for_draft` while a required
    clarification remains pending.

### A3. Add the AssemblyAI boundary

- [ ] **Complete:** Define a `TranscriptionService` interface and a fake
  implementation for route and integration tests.
  - [ ] **Verify:** Tests can produce a deterministic transcript without an
    AssemblyAI credential or network call.

- [ ] **Complete:** Implement the AssemblyAI adapter behind that interface.
  The adapter receives audio from the transcription endpoint and returns text
  for the current MVP flow.
  - [ ] **Verify:** A mocked provider test covers success, empty transcript,
    and provider failure; none changes the public API response shape.

- [ ] **Complete:** Add `AI_ENGINE_ASSEMBLYAI_API_KEY` to
  `ai_engine/.env.example` and configuration, with the fake transcriber used
  whenever the real adapter is not configured.
  - [ ] **Verify:** The normal test suite runs without the key, while an
    opt-in local smoke test can use the real adapter without exposing its key to
    the Astro application.

- [ ] **Complete:** Save the user-reviewed transcription as `case_text` rather
  than persisting raw provider events or transcript history.
  - [ ] **Verify:** A corrected transcript is the exact text supplied to the
    extraction service.

### A4. Extract, clarify, and draft

- [ ] **Complete:** Define a `CaseIntelligenceService` interface that returns
  provider, service, issue category, summary, attempted resolutions, desired
  outcome, and missing fields from `case_text`.
  - [ ] **Verify:** Fixture tests cover the Converge connectivity example and
    one incomplete case that requires clarification.

- [ ] **Complete:** Implement the first extraction adapter. It may be a simple
  deterministic implementation or the selected model provider, but it must
  validate its result through the Pydantic case model.
  - [ ] **Verify:** Extraction produces `clarifying` only when one of the three
    MVP clarification fields is absent; otherwise it produces `ready_for_draft`.

- [ ] **Complete:** Generate one factual `support_draft` only when the case is
  ready for drafting.
  - [ ] **Verify:** Draft tests confirm that known case details appear in the
    subject/body and blank required details prevent generation.

- [ ] **Complete:** Support user edits to the draft without adding sending or
  provider-integration behavior.
  - [ ] **Verify:** Updating the draft returns `draft_ready` and persists the
    edited subject and body through the repository.

### A5. Integrate Supabase persistence

- [ ] **Complete:** Implement a Supabase-backed `CaseRepository` after Person
  B's migration and schema verification are available.
  - [ ] **Verify:** The same repository contract tests pass against local
    Supabase after `supabase db reset`.

- [ ] **Complete:** Map `support_case`, `case_clarification`, and
  `support_draft` rows to the shared API payload without leaking database-only
  details.
  - [ ] **Verify:** Loading a case returns ordered clarifications and either
    `draft: null` or the one current draft.

## Handoff to Person B

Provide Person B with:

- a running local API URL and the exact environment variable used for it;
- the shared JSON fixtures and a fixture-backed API mode;
- the endpoint list and example `curl` or HTTP-client requests;
- a list of user-facing errors for transcription, extraction, clarification,
  and draft generation; and
- confirmation that endpoint names and snake_case response fields match the
  shared contract.

## Done for Person A

Person A's track is ready for integration when the API can complete the full
typed flow against the in-memory repository, then repeat it against Person B's
local Supabase schema without changing the public contract. The voice endpoint
must also work with the fake transcription service before the real AssemblyAI
adapter is connected.
