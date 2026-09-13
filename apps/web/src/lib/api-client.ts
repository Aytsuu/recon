/**
 * RECON API Client
 *
 * Implements every endpoint from the shared API contract
 * (context-factory/docs/implementation-plan.md).
 *
 * Mode is controlled by the PUBLIC_API_MODE environment variable:
 *   PUBLIC_API_MODE=mock   → returns fixture data (default in development)
 *   PUBLIC_API_MODE=api    → calls the FastAPI server at PUBLIC_API_BASE_URL
 *
 * All payloads use snake_case field names so no translation layer is needed
 * between FastAPI models, the database columns, and this client.
 */

import type {
  CaseResponse,
  TranscribeResponse,
  CreateCasePayload,
  PatchCasePayload,
  PatchClarificationPayload,
  PatchDraftPayload,
} from './types.js';
import FIXTURES from '../fixtures/cases.json';

// ---------------------------------------------------------------------------
// Runtime configuration
// ---------------------------------------------------------------------------
const API_MODE =
  (import.meta.env.PUBLIC_API_MODE as string | undefined) ?? 'mock';

const API_BASE_URL =
  (import.meta.env.PUBLIC_API_BASE_URL as string | undefined) ??
  'http://127.0.0.1:8000';

const isMock = API_MODE === 'mock';

// ---------------------------------------------------------------------------
// Fixture helper
// ---------------------------------------------------------------------------
function pickFixture(caseId: number): CaseResponse {
  if (caseId === 1) return FIXTURES.input_ready_typed as CaseResponse;
  if (caseId === 2) return FIXTURES.clarifying_typed as CaseResponse;
  if (caseId === 3) return FIXTURES.draft_ready_typed as CaseResponse;
  if (caseId === 4) return FIXTURES.voice_transcribing as CaseResponse;
  return FIXTURES.input_ready_typed as CaseResponse;
}

let mockNextId = 5;

// ---------------------------------------------------------------------------
// HTTP helper (real API mode)
// ---------------------------------------------------------------------------
async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${init?.method ?? 'GET'} ${url} → ${res.status}: ${text}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// POST /api/cases
// ---------------------------------------------------------------------------
export async function createCase(
  payload: CreateCasePayload,
): Promise<CaseResponse> {
  if (isMock) {
    const fixture =
      payload.input_mode === 'voice'
        ? (FIXTURES.voice_transcribing as CaseResponse)
        : (FIXTURES.input_ready_typed as CaseResponse);

    // Return a shallow copy with a unique mock id.
    return {
      data: { ...fixture.data, id: mockNextId++ },
    } as CaseResponse;
  }

  return apiFetch<CaseResponse>('/api/cases', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// GET /api/cases/:case_id
// ---------------------------------------------------------------------------
export async function getCase(caseId: number): Promise<CaseResponse> {
  if (isMock) {
    return pickFixture(caseId);
  }

  return apiFetch<CaseResponse>(`/api/cases/${caseId}`);
}

// ---------------------------------------------------------------------------
// PATCH /api/cases/:case_id
// ---------------------------------------------------------------------------
export async function patchCase(
  caseId: number,
  payload: PatchCasePayload,
): Promise<CaseResponse> {
  if (isMock) {
    const base = pickFixture(caseId);
    return { data: { ...base.data, ...payload } } as CaseResponse;
  }

  return apiFetch<CaseResponse>(`/api/cases/${caseId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// POST /api/cases/:case_id/transcribe
// ---------------------------------------------------------------------------
export async function transcribeCase(
  caseId: number,
  audio: Blob,
): Promise<TranscribeResponse> {
  if (isMock) {
    return FIXTURES.transcribe_response as TranscribeResponse;
  }

  const form = new FormData();
  form.append('audio', audio, 'recording.webm');

  return apiFetch<TranscribeResponse>(`/api/cases/${caseId}/transcribe`, {
    method: 'POST',
    headers: {}, // let browser set multipart boundary
    body: form,
  });
}

// ---------------------------------------------------------------------------
// POST /api/cases/:case_id/extract
// ---------------------------------------------------------------------------
export async function extractCase(caseId: number): Promise<CaseResponse> {
  if (isMock) {
    return FIXTURES.clarifying_typed as CaseResponse;
  }

  return apiFetch<CaseResponse>(`/api/cases/${caseId}/extract`, {
    method: 'POST',
  });
}

// ---------------------------------------------------------------------------
// PATCH /api/cases/:case_id/clarifications/:clarification_id
// ---------------------------------------------------------------------------
export async function patchClarification(
  caseId: number,
  clarificationId: number,
  payload: PatchClarificationPayload,
): Promise<CaseResponse> {
  if (isMock) {
    const base = pickFixture(caseId);
    const updatedClarifications = base.data.clarifications.map((c) =>
      c.id === clarificationId ? { ...c, ...payload } : c,
    );
    return {
      data: { ...base.data, clarifications: updatedClarifications },
    } as CaseResponse;
  }

  return apiFetch<CaseResponse>(
    `/api/cases/${caseId}/clarifications/${clarificationId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
  );
}

// ---------------------------------------------------------------------------
// POST /api/cases/:case_id/draft
// ---------------------------------------------------------------------------
export async function generateDraft(caseId: number): Promise<CaseResponse> {
  if (isMock) {
    return FIXTURES.draft_ready_typed as CaseResponse;
  }

  return apiFetch<CaseResponse>(`/api/cases/${caseId}/draft`, {
    method: 'POST',
  });
}

// ---------------------------------------------------------------------------
// PATCH /api/cases/:case_id/draft
// ---------------------------------------------------------------------------
export async function patchDraft(
  caseId: number,
  payload: PatchDraftPayload,
): Promise<CaseResponse> {
  if (isMock) {
    const base = FIXTURES.draft_ready_typed as CaseResponse;
    return {
      data: {
        ...base.data,
        draft: base.data.draft ? { ...base.data.draft, ...payload } : null,
      },
    } as CaseResponse;
  }

  return apiFetch<CaseResponse>(`/api/cases/${caseId}/draft`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// DELETE /api/cases/:case_id
// ---------------------------------------------------------------------------
export async function deleteCase(caseId: number): Promise<CaseResponse> {
  if (isMock) {
    return pickFixture(caseId);
  }

  return apiFetch<CaseResponse>(`/api/cases/${caseId}`, {
    method: 'DELETE',
  });
}

// ---------------------------------------------------------------------------
// GET /api/cases/search
// ---------------------------------------------------------------------------
export async function searchCases(
  payload: import('./types.js').SearchCasesData = {},
): Promise<import('./types.js').SearchCasesResponse> {
  if (isMock) {
    const all = [
      FIXTURES.input_ready_typed.data,
      FIXTURES.clarifying_typed.data,
      FIXTURES.draft_ready_typed.data,
      FIXTURES.voice_transcribing.data,
    ] as import('./types.js').SupportCase[];

    const filtered = payload.query
      ? all.filter(
          (c) =>
            c.case_text?.toLowerCase().includes(payload.query!.toLowerCase()) ||
            c.provider_name?.toLowerCase().includes(payload.query!.toLowerCase()),
        )
      : all;

    const page = payload.page ?? 1;
    const limit = payload.limit ?? 10;
    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    return {
      data: paginated,
      total: filtered.length,
      page,
      next_page: start + limit < filtered.length ? page + 1 : undefined,
      previous_page: page > 1 ? page - 1 : undefined,
    };
  }

  const queryParams = new URLSearchParams();
  Object.entries(payload).forEach(([k, v]) => {
    if (v !== undefined && v !== null) queryParams.append(k, String(v));
  });

  return apiFetch<import('./types.js').SearchCasesResponse>(
    `/api/cases/search?${queryParams.toString()}`,
  );
}

