# Person B Plan: Web and Supabase

**Owner:** Person B  
**Workspaces:** `apps/web/` and `supabase/` only  
**Shared contract:** [Parallel Implementation Plan](../docs/implementation-plan.md)

## Responsibility

Person B owns the Astro user experience and the Supabase migration that stores
the feature's cases. The web app talks to FastAPI through the shared API
contract; it does not query Supabase tables directly.

Do not add a browser Supabase client for this feature. FastAPI is the only
application client of the three case tables.

Person B does not edit `ai_engine/`. Person A owns the API, AssemblyAI adapter,
extraction, clarification, draft logic, and server-side database repository.

## Supabase migration

Create one follow-up migration through the Supabase CLI. Keep the existing
placeholder migration unchanged. The feature needs only these tables:

```text
support_case
  |- case_clarification (zero or more focused questions)
  `- support_draft      (zero or one current editable draft)
```

### `support_case`

| Column | Type and rule |
| --- | --- |
| `id` | `bigint generated always as identity primary key` |
| `input_mode` | `text not null`; `typed` or `voice` |
| `status` | `text not null default 'input_ready'`; one of `transcribing`, `input_ready`, `clarifying`, `ready_for_draft`, `draft_ready`, `failed` |
| `case_text` | `text`; typed problem or user-reviewed transcript |
| `language_code` | Optional `text` |
| `provider_name` | Optional `text` |
| `service_name` | Optional `text` |
| `issue_category` | Optional `text` |
| `problem_summary` | Optional `text` |
| `attempted_resolutions` | `text[] not null default '{}'` |
| `desired_outcome` | Optional `text` |
| `created_at`, `updated_at` | `timestamptz not null default now()` |

Add checks that:

- `input_mode` is `typed` or `voice`;
- `status` is one of the listed feature states;
- non-null `case_text` is not whitespace only;
- a typed case has `case_text`; and
- only a voice case can be `transcribing`.

### `case_clarification`

| Column | Type and rule |
| --- | --- |
| `id` | `bigint generated always as identity primary key` |
| `case_id` | `bigint not null references support_case(id) on delete cascade` |
| `field_key` | `text not null`; `provider_name`, `problem_summary`, or `desired_outcome` |
| `question` | `text not null` |
| `answer` | Optional `text` |
| `status` | `text not null default 'pending'`; `pending`, `answered`, or `skipped` |
| `position` | `smallint not null`, greater than zero |
| `created_at` | `timestamptz not null default now()` |
| `answered_at` | Optional `timestamptz` |

Add `unique (case_id, field_key)` and `unique (case_id, position)`. Enforce
that pending/skipped questions have no answer or answer timestamp, while an
answered question has both a non-blank answer and `answered_at`.

### `support_draft`

| Column | Type and rule |
| --- | --- |
| `id` | `bigint generated always as identity primary key` |
| `case_id` | `bigint not null unique references support_case(id) on delete cascade` |
| `subject` | `text not null` and not blank |
| `body` | `text not null` and not blank |
| `language_code` | Optional `text` |
| `created_at`, `updated_at` | `timestamptz not null default now()` |

Add `support_case_created_at_idx` on `support_case (created_at desc)`. The
primary and unique keys cover the initial child-table lookups, so do not add
more indexes yet.

### Supabase tasks

- [ ] **Complete:** Generate the migration with the Supabase CLI and implement
  the three tables, checks, foreign keys, unique keys, and one list index.
  - [ ] **Verify:** `supabase db reset` succeeds and `supabase migration list
    --local` shows the new migration after the placeholder baseline.

- [ ] **Complete:** Enable RLS on the three public tables without creating the
  deferred user-specific policy model.
  - [ ] **Verify:** The Astro application has no direct Supabase table client or
    query; all development case data is reached through FastAPI.

- [ ] **Complete:** Add a small development fixture: one `input_ready` typed
  case, one `clarifying` case with a pending question, and one `draft_ready`
  case with a draft.
  - [ ] **Verify:** Person A can use the fixture database to load ordered
    clarifications, the one current draft, and cascade-delete a case.

## Astro frontend

### B1. Create the API client and fixture mode

- [ ] **Complete:** Add an `apps/web` API client that implements the shared
  endpoints and snake_case payloads from the coordination plan.
  - [ ] **Verify:** Client tests consume the shared JSON fixtures without
    renaming fields or depending on a running API.

- [ ] **Complete:** Add a development switch between fixture responses and the
  local FastAPI base URL.
  - [ ] **Verify:** The same screen renders an empty case, a clarifying case,
    and a draft-ready case from both client modes.

- [ ] **Complete:** Document non-secret browser settings for the client, such
  as `PUBLIC_API_MODE=mock` and `PUBLIC_API_BASE_URL=http://127.0.0.1:8000`.
  - [ ] **Verify:** A developer can start in mock mode without Person A's API,
    then switch to API mode without changing component data shapes.

### B2. Build the typed case flow first

- [ ] **Complete:** Replace the starter `index.astro` with the initial problem
  form: typed description, optional provider, and create-case action.
  - [ ] **Verify:** Submitting fixture-backed text creates and displays an
    `input_ready` case state.

- [ ] **Complete:** Build the case-review screen: current `case_text`,
  extracted fields, clarification questions, and current state.
  - [ ] **Verify:** The fixture-backed UI can show all shared case states and
    sends user edits through the corresponding API-client operations.

- [ ] **Complete:** Build the clarification form with ordered questions and
  answer/skip controls.
  - [ ] **Verify:** Answering or skipping a fixture question refreshes the case
    view using the returned complete case payload.

- [ ] **Complete:** Build the draft-review screen with editable subject/body,
  regeneration state, and a copy-to-clipboard action.
  - [ ] **Verify:** A draft-ready fixture is editable and copyable, while a
    missing or stale draft does not show a copy action.

### B3. Add voice input after the typed flow works

> **Scope correction (2026-09-12):** The original B3 description assumed a
> "record audio blob → POST to `/transcribe`" flow. Verification found the
> project uses AssemblyAI realtime streaming STT, not pre-recorded upload-and-
> poll. B3 is revised to match the realtime streaming design. The AI Engine
> only issues a short-lived token (A3); the browser owns the WebSocket session.

- [ ] **Complete:** Add a browser recorder with start, stop, permission-denied,
  and typed-fallback states. Capture live microphone audio as mono 16-bit PCM
  (default) or Opus frames according to the configured encoding.
  - [ ] **Verify:** A repeatable manual or browser test covers all four recorder
    states without requiring a real AssemblyAI key.

- [ ] **Complete:** On recording start, fetch a short-lived token from
  `POST /api/cases/{case_id}/transcription-token`. Open a WebSocket to
  `wss://streaming.assemblyai.com/v3/ws?token=<token>&sample_rate=…&encoding=…`.
  Send audio frames as binary WebSocket messages. Never expose the permanent
  API key in browser code or URLs.
  - [ ] **Verify:** A mocked token response and mocked WebSocket confirm the
    connection is opened with the correct URL parameters and that no key value
    appears in client-side code.

- [ ] **Complete:** Handle incoming AssemblyAI `Turn` events: render interim
  turns as live preview text. When `end_of_turn: true` arrives, append the
  finalized text to the editable review area. On recording stop, send
  `{"type":"Terminate"}` and close the socket.
  - [ ] **Verify:** A simulated event sequence (interim → final → Terminate)
    produces the expected editable review text without a live API call.

- [ ] **Complete:** After streaming ends, display the accumulated finalized
  turns as editable review text and send the user-reviewed text through the
  existing `PATCH /api/cases/{case_id}` to persist `case_text` and advance
  the voice case from `transcribing` to `input_ready`.
  - [ ] **Verify:** The mocked PATCH request carries the exact reviewed text
    and the UI reflects the resulting `input_ready` case state.

### B4. Connect and polish

- [ ] **Complete:** Switch the API client to Person A's running local FastAPI
  service after the shared contract tests pass.
  - [ ] **Verify:** A typed case completes create, extract, clarify, draft, edit,
    and copy against the real API and local Supabase database.

- [ ] **Complete:** Add concise UI errors, loading states, back navigation,
  empty states, and responsive layout to the core screens.
  - [ ] **Verify:** The sample typed and voice flows remain understandable at
    desktop and mobile widths.

## Handoff to Person A

Provide Person A with:

- the migration name and confirmation that `supabase db reset` succeeds;
- the exact tables, constraints, and fixture records described above;
- the local Supabase connection configuration needed by the server-side
  repository; and
- confirmation that the web client uses the shared snake_case API contract and
  never reads the new tables directly.

## Done for Person B

Person B's track is ready for integration when the web completes the typed flow
with fixture responses, the migration resets cleanly, and the API client can be
pointed at Person A's local service without changing component data shapes.