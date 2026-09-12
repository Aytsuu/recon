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

- [ ] **Complete:** Add Pydantic request and response models matching the shared
  `Case` payload, clarification payload, draft payload, and endpoint requests.
  - [ ] **Verify:** API-schema tests accept the shared JSON fixtures and reject
    malformed state, blank typed input, and invalid clarification answers.

- [ ] **Complete:** Add route modules for cases, transcription, extraction,
  clarifications, and drafts under `ai_engine/app/api/routes/`.
  - [ ] **Verify:** Each route is registered under `/api`, returns the agreed
    response shape, and leaves `GET /health` unchanged.

- [ ] **Complete:** Define a small `CaseRepository` interface for create, load,
  update, clarification, draft, and delete operations.
  - [ ] **Verify:** Repository contract tests pass against an in-memory
    implementation before the Supabase-backed implementation exists.

### A2. Implement the case state machine

- [ ] **Complete:** Implement typed case creation as `input_ready` and empty
  voice case creation as `transcribing`.
  - [ ] **Verify:** API tests prove the two creation modes return the expected
    state and reject invalid combinations of mode, status, and `case_text`.

- [ ] **Complete:** Implement case updates for reviewed `case_text`, provider,
  service, category, summary, attempted resolutions, and desired outcome.
  - [ ] **Verify:** A material edit removes the existing draft and returns a
    case to `input_ready` or `ready_for_draft` as required by the shared plan.

- [ ] **Complete:** Implement clarification answers and skipped questions.
  - [ ] **Verify:** A case cannot become `ready_for_draft` while a required
    clarification remains pending.

### A3. Add the AssemblyAI streaming token boundary

> **Scope correction (2026-09-12):** The original A3 description was written
> for a pre-recorded upload-and-poll adapter. Verification found this design is
> incompatible with the project's realtime streaming STT approach. A3 is
> revised to a narrowly-scoped server-side token issuer. The uncommitted
> upload-and-poll code is superseded by this description. Browser WebSocket
> streaming and Turn handling belong to B3.

- [ ] **Complete:** Replace the A1 `501` stub at
  `POST /api/cases/{case_id}/transcription-token` with a token-issuance
  endpoint that issues a short-lived AssemblyAI streaming token for a voice
  case in `transcribing` status.
  - [ ] **Verify:** Route returns `404 case_not_found` for an unknown case,
    `409 invalid_case_state` for a typed or non-transcribing case, and a
    `200` success envelope on a valid request. The case status and `case_text`
    are unchanged after the call.

- [ ] **Complete:** Define a `StreamingTokenService` protocol with an
  `issue_token(expires_in_seconds)` method returning a `StreamingTokenResult`
  (`token`, `expires_in_seconds`). Provide a deterministic
  `FakeStreamingTokenService` that requires no key and no network call.
  - [ ] **Verify:** Tests override the dependency with the fake and assert the
    exact token envelope; the normal suite passes offline.

- [ ] **Complete:** Implement an `AssemblyAIStreamingTokenService` that calls
  `GET https://streaming.assemblyai.com/v3/token?expires_in_seconds=60`
  with header `authorization: <key>` (no `Bearer` prefix) and returns the
  token. Return `502 token_issuance_failed` or `503 token_service_unavailable`
  on failure; never expose the key in a response or log.
  - [ ] **Verify:** Unit tests use an injected mock HTTP client to cover
    success and transport failure without making real requests.

- [ ] **Complete:** Add `AI_ENGINE_ASSEMBLYAI_API_KEY=` to `.env.example` and
  config. Use the fake when the key is absent; use the real adapter when it is
  set.
  - [ ] **Verify:** Dependency-selection test confirms no-key → fake and
    key-set → AssemblyAI adapter. No opt-in audio file is needed because this
    endpoint only issues a token.

Token success response shape:

```json
{
  "data": {
    "case_id": 123,
    "token": "<short-lived-token>",
    "expires_in_seconds": 60,
    "ws_url": "wss://streaming.assemblyai.com/v3/ws"
  }
}
```

The AI Engine does not open the WebSocket, stream audio, or process Turn
events. Reviewed transcript text is persisted only via the existing
`PATCH /api/cases/{case_id}` flow (unchanged from A2).

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
local Supabase schema without changing the public contract. The token endpoint
must issue a valid short-lived token using the fake service before the real
AssemblyAI adapter is connected.