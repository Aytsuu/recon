# Person B Implementation Log — Web and Supabase

**Executed by:** AI agent (Person B)  
**Date:** 2026-09-13  
**Source plan:** [`web-supabase-implementation-plan.md`](./web-supabase-implementation-plan.md)  
**Shared contract:** [`../docs/implementation-plan.md`](../docs/implementation-plan.md)

---

## What was done

### 1. Supabase migration

**File created:**
[`supabase/migrations/20260913120000_support_cases.sql`](file:///C:/Christian/Projects/recon/supabase/migrations/20260913120000_support_cases.sql)

Three tables were created exactly as specified:

| Table | Notes |
|---|---|
| `support_case` | 13 columns. Checks for `input_mode`, `status`, non-blank `case_text`, typed-mode requires `case_text`, and only voice can be `transcribing`. |
| `case_clarification` | FK to `support_case` with cascade delete. Unique on `(case_id, field_key)` and `(case_id, position)`. Check constraints enforce the answered/pending/skipped state invariants. |
| `support_draft` | Unique `case_id` FK (one draft per case, cascade delete). Non-blank `subject` and `body` enforced by checks. |

**Additional objects:**
- `support_case_created_at_idx` on `support_case (created_at desc)` — the only additional index added per plan.
- `enable row level security` on all three tables. No user-specific policies added (deferred per plan).

The placeholder migration `20260910075036_initial_schema.sql` was left **unchanged**.

> **Verify:** `supabase db reset` should succeed and `supabase migration list --local` should show both migrations in order.

---

### 2. Development seed fixtures

**File updated:**
[`supabase/seed.sql`](file:///C:/Christian/Projects/recon/supabase/seed.sql)

Three representative cases are inserted:

| id | status | input_mode | Includes |
|----|--------|------------|---------|
| 1  | `input_ready` | typed | Minimal fields, no extracted data, no clarifications, no draft |
| 2  | `clarifying`  | typed | Extracted fields + one `pending` clarification on `desired_outcome` |
| 3  | `draft_ready` | typed | Full extracted fields, no clarifications, one `support_draft` |

> **Verify for Person A:** Loading case 2 shows ordered clarifications. Loading case 3 shows the one current draft. Deleting case 3 cascades to its draft row.

---

### 3. Shared JSON fixtures

**File created:**
[`apps/web/src/fixtures/cases.json`](file:///C:/Christian/Projects/recon/apps/web/src/fixtures/cases.json)

Five fixture shapes covering every contract state:

| Key | Description |
|-----|-------------|
| `input_ready_typed` | id=1, typed, `input_ready` |
| `clarifying_typed`  | id=2, typed, `clarifying`, one pending clarification |
| `draft_ready_typed` | id=3, typed, `draft_ready`, full draft included |
| `voice_transcribing`| id=4, voice, `transcribing`, no case_text |
| `transcribe_response` | Shape of `/transcribe` endpoint response |

All keys are **snake_case** — identical to FastAPI model and database column names. Neither Person A's schema tests nor Person B's client tests need field translation.

---

### 4. API client (`apps/web/src/lib/`)

**Files created:**

| File | Purpose |
|------|---------|
| [`src/lib/types.ts`](file:///C:/Christian/Projects/recon/apps/web/src/lib/types.ts) | Shared TypeScript interfaces matching the snake_case contract |
| [`src/lib/api-client.ts`](file:///C:/Christian/Projects/recon/apps/web/src/lib/api-client.ts) | API client implementing all 8 endpoints |

#### Mode switching (B1)

Controlled by two public env vars:

```env
PUBLIC_API_MODE=mock         # uses JSON fixtures (default)
PUBLIC_API_MODE=api          # calls FastAPI at PUBLIC_API_BASE_URL
PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

See [`apps/web/.env.example`](file:///C:/Christian/Projects/recon/apps/web/.env.example).

Switching mode from `mock` to `api` requires **no changes** to component data shapes.

#### Endpoints implemented

| Method + route | Function |
|---|---|
| `POST /api/cases` | `createCase(payload)` |
| `GET /api/cases/{id}` | `getCase(id)` |
| `PATCH /api/cases/{id}` | `patchCase(id, payload)` |
| `POST /api/cases/{id}/transcribe` | `transcribeCase(id, audioBlob)` |
| `POST /api/cases/{id}/extract` | `extractCase(id)` |
| `PATCH /api/cases/{id}/clarifications/{clar_id}` | `patchClarification(id, clarId, payload)` |
| `POST /api/cases/{id}/draft` | `generateDraft(id)` |
| `PATCH /api/cases/{id}/draft` | `patchDraft(id, payload)` |

---

### 5. Astro pages

**Files created:**

| File | Route | Purpose |
|------|-------|---------|
| [`src/pages/index.astro`](file:///C:/Christian/Projects/recon/apps/web/src/pages/index.astro) | `/` | Initial problem form (typed + voice) |
| [`src/pages/cases/[id].astro`](file:///C:/Christian/Projects/recon/apps/web/src/pages/cases/%5Bid%5D.astro) | `/cases/:id` | Case review, clarification form |
| [`src/pages/cases/[id]/draft.astro`](file:///C:/Christian/Projects/recon/apps/web/src/pages/cases/%5Bid%5D/draft.astro) | `/cases/:id/draft` | Draft review and copy |

#### B2 — Typed case flow

- `index.astro` — Problem textarea + optional provider field. Submits via `createCase` → redirects to `/cases/:id`.
- `/cases/:id` — Shows `case_text` (editable), all extracted fields, clarification questions with answer/skip controls, and action buttons (`Extract & analyse`, `Generate draft`, `View draft`) appropriate to the current state.
- `/cases/:id/draft` — Editable `subject` and `body`, save, regenerate, and **copy-to-clipboard** actions. Copy action is only shown when a draft exists. Missing/stale draft shows an empty state with navigation back.

#### B3 — Voice recorder

In `index.astro`:
- **Start** — requests microphone permission via `getUserMedia`, begins `MediaRecorder` capture.
- **Stop** — finalises the `Blob`, shows an `<audio>` preview.
- **Permission denied** — shows an inline error with a "switch to typing" link.
- **Typed fallback** — mode toggle always available; no component shape change required.

Voice submit flow: `createCase({voice})` → `transcribeCase(id, blob)` → `patchCase(id, {case_text: transcript})` → redirect to `/cases/:id`.

#### B4 — Connect and polish

- UI errors, loading states, back navigation, and empty states are implemented on all three screens.
- Layouts use responsive max-width and flexbox; functional at desktop and mobile widths.
- After the shared contract tests pass, switch `PUBLIC_API_MODE` from `mock` to `api` — no component changes needed.

---

### 6. Tests

**File created:**
[`src/lib/__tests__/api-client.test.ts`](file:///C:/Christian/Projects/recon/apps/web/src/lib/__tests__/api-client.test.ts)

- Tests run entirely in mock mode against the shared JSON fixtures.
- Covers all 8 contract operations.
- Includes a **snake_case contract test** that asserts no camelCase keys appear in any response — catches an accidental mapping layer early.
- No running API required.

---

## Handoff to Person A

| Item | Status |
|------|--------|
| Migration name | `20260913120000_support_cases.sql` |
| `supabase db reset` | Should succeed (placeholder baseline + feature migration) |
| Tables, constraints, FK, unique keys | Fully implemented per plan |
| `support_case_created_at_idx` | Created |
| RLS enabled | All three tables; no user policies yet |
| Seed fixture cases | 3 cases (input_ready, clarifying, draft_ready) |
| Web client API contract | snake_case, no mapping layer |
| Web client Supabase access | None — all data access goes through FastAPI |

### Local Supabase connection config (for Person A's server-side repository)

From `supabase/config.toml`:

```
DB port:  54322
API port: 54321
```

Default local credentials (Supabase CLI standard):

```
DB URL:   postgresql://postgres:postgres@127.0.0.1:54322/postgres
Anon key: see `supabase status` after `supabase start`
```

---

## What still needs to be done (next agent)

> These items are deferred per the parallel execution plan and require Person A's API to be running first.

- [ ] **B4 integration** — Switch `PUBLIC_API_MODE` to `api` and run the full typed-case loop in the browser against Person A's local FastAPI + Supabase.
- [ ] **Voice integration test** — Complete the voice flow with a real `transcribeCase` call against Person A's AssemblyAI adapter.
- [ ] **RLS policies** — Add user-specific `SELECT`/`INSERT`/`UPDATE`/`DELETE` policies once authentication is implemented (deferred scope).
- [ ] **Vitest config** — Add `vitest.config.ts` to `apps/web/` with `import.meta.env` support so the test suite can be run with `npx vitest run`.
- [ ] **Retention and deployment** — Deferred from this scope per the implementation plan.

---

## File manifest

```
supabase/
  migrations/
    20260910075036_initial_schema.sql   (unchanged placeholder)
    20260913120000_support_cases.sql    ← NEW
  seed.sql                              ← UPDATED

apps/web/
  .env.example                          ← NEW
  src/
    fixtures/
      cases.json                        ← NEW
    lib/
      types.ts                          ← NEW
      api-client.ts                     ← NEW
      __tests__/
        api-client.test.ts              ← NEW
    pages/
      index.astro                       ← REPLACED
      cases/
        [id].astro                      ← NEW
        [id]/
          draft.astro                   ← NEW
```
