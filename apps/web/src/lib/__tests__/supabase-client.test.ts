/**
 * Supabase client unit tests — mocks @supabase/supabase-js, no shared fixtures.
 *
 * Run:
 *   npx vitest run src/lib/__tests__/supabase-client.test.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { CaseResponse } from '../types.js';

const inputReady: CaseResponse = {
  data: {
    id: 1,
    input_mode: 'typed',
    status: 'input_ready',
    case_text: 'My internet keeps disconnecting every few hours.',
    language_code: 'en',
    provider_name: 'Converge ICT',
    service_name: 'Residential fiber internet',
    issue_category: null,
    problem_summary: null,
    attempted_resolutions: [],
    desired_outcome: null,
    support_email: null,
    support_phone: null,
    support_url: null,
    clarifications: [],
    draft: null,
  },
};

const clarifying: CaseResponse = {
  data: {
    id: 2,
    input_mode: 'typed',
    status: 'clarifying',
    case_text: 'My bill shows unexpected charges for last month.',
    language_code: 'en',
    provider_name: 'Globe Telecom',
    service_name: 'Postpaid mobile plan',
    issue_category: 'billing',
    problem_summary: 'Unexpected charges on monthly bill.',
    attempted_resolutions: ['Checked the bill breakdown online'],
    desired_outcome: null,
    support_email: null,
    support_phone: null,
    support_url: null,
    clarifications: [
      {
        id: 1,
        field_key: 'desired_outcome',
        question: 'What resolution are you expecting?',
        answer: null,
        status: 'pending',
        position: 1,
      },
    ],
    draft: null,
  },
};

const draftReady: CaseResponse = {
  data: {
    id: 3,
    input_mode: 'typed',
    status: 'draft_ready',
    case_text: 'My fiber connection has been dropping for three days.',
    language_code: 'en',
    provider_name: 'PLDT Home',
    service_name: 'Home Fiber Broadband',
    issue_category: 'internet_connectivity',
    problem_summary: 'Persistent fiber connection drops over three days.',
    attempted_resolutions: ['Restarted the ONT', 'Restarted the router'],
    desired_outcome: 'Restore stable 24/7 fiber connection or dispatch a technician.',
    support_email: null,
    support_phone: null,
    support_url: null,
    clarifications: [],
    draft: {
      id: 1,
      subject: 'Persistent Fiber Connection Drops',
      body: 'Dear PLDT Home Support,\n\nI am writing to report an ongoing issue.',
      language_code: 'en',
    },
  },
};

function toDbRow(caseData: CaseResponse['data']) {
  return {
    id: caseData.id,
    input_mode: caseData.input_mode,
    status: caseData.status,
    case_text: caseData.case_text,
    language_code: caseData.language_code,
    provider_name: caseData.provider_name,
    service_name: caseData.service_name,
    issue_category: caseData.issue_category,
    problem_summary: caseData.problem_summary,
    attempted_resolutions: caseData.attempted_resolutions,
    desired_outcome: caseData.desired_outcome,
    support_email: caseData.support_email,
    support_phone: caseData.support_phone,
    support_url: caseData.support_url,
    case_clarification: caseData.clarifications.map((c) => ({
      id: c.id,
      field_key: c.field_key,
      question: c.question,
      answer: c.answer,
      status: c.status,
      position: c.position,
    })),
    support_draft: caseData.draft
      ? {
          id: caseData.draft.id,
          subject: caseData.draft.subject,
          body: caseData.draft.body,
          language_code: caseData.draft.language_code,
        }
      : null,
  };
}

type QueryResult = { data: unknown; error: null } | { data: null; error: { message: string } };

const { mockFrom, mockCreateClient } = vi.hoisted(() => {
  const mockFrom = vi.fn();
  const mockCreateClient = vi.fn(() => ({ from: mockFrom }));
  return { mockFrom, mockCreateClient };
});

vi.mock('@supabase/supabase-js', () => ({
  createClient: mockCreateClient,
}));

function mockQuery(result: QueryResult) {
  const chain = {
    select: vi.fn(() => chain),
    insert: vi.fn(() => chain),
    update: vi.fn(() => chain),
    delete: vi.fn(() => chain),
    eq: vi.fn(() => chain),
    or: vi.fn(() => chain),
    order: vi.fn(() => chain),
    range: vi.fn(() => Promise.resolve({ ...result, count: Array.isArray(result.data) ? result.data.length : 1 })),
    single: vi.fn(() => Promise.resolve(result)),
  };
  mockFrom.mockReturnValue(chain);
  return chain;
}

vi.stubEnv('PUBLIC_SUPABASE_URL', 'http://127.0.0.1:54321');
vi.stubEnv('PUBLIC_SUPABASE_ANON_KEY', 'test-anon-key');

const {
  createCase,
  getCase,
  patchCase,
  patchClarification,
  patchDraft,
} = await import('../supabase-client.js');

describe('supabase-client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('createCase inserts a typed case', async () => {
    const row = toDbRow({ ...inputReady.data, id: 10 });
    mockQuery({ data: row, error: null });

    const res = await createCase({
      input_mode: 'typed',
      case_text: 'My internet keeps disconnecting every few hours.',
    });

    expect(res.data.input_mode).toBe('typed');
    expect(res.data.status).toBe('input_ready');
    expect(mockCreateClient).toHaveBeenCalledWith('http://127.0.0.1:54321', 'test-anon-key');
  });

  it('getCase returns a mapped case', async () => {
    mockQuery({ data: toDbRow(inputReady.data), error: null });

    const res = await getCase(1);
    expect(res.data).toMatchObject({ id: 1, status: 'input_ready' });
  });

  it('patchCase merges updates', async () => {
    mockQuery({
      data: toDbRow({ ...inputReady.data, provider_name: 'Globe' }),
      error: null,
    });

    const res = await patchCase(1, { provider_name: 'Globe' });
    expect(res.data.provider_name).toBe('Globe');
    expect(res.data.status).toBe('input_ready');
  });

  it('patchClarification marks a clarification as answered', async () => {
    const answered = {
      ...clarifying.data,
      clarifications: clarifying.data.clarifications.map((c) =>
        c.id === 1 ? { ...c, status: 'answered' as const, answer: 'I want a full refund.' } : c,
      ),
      desired_outcome: 'I want a full refund.',
      status: 'ready_for_draft' as const,
    };

    mockFrom
      .mockReturnValueOnce({
        select: vi.fn(() => ({
          eq: vi.fn(() => ({
            single: vi.fn(() => Promise.resolve({ data: toDbRow(clarifying.data), error: null })),
          })),
        })),
      })
      .mockReturnValueOnce({
        update: vi.fn(() => ({
          eq: vi.fn(() => Promise.resolve({ error: null })),
        })),
      })
      .mockReturnValueOnce({
        select: vi.fn(() => ({
          eq: vi.fn(() => ({
            single: vi.fn(() => Promise.resolve({ data: toDbRow(clarifying.data), error: null })),
          })),
        })),
      })
      .mockReturnValueOnce({
        update: vi.fn(() => ({
          eq: vi.fn(() => ({
            select: vi.fn(() => ({
              single: vi.fn(() => Promise.resolve({ data: toDbRow(answered), error: null })),
            })),
          })),
        })),
      });

    const res = await patchClarification(2, 1, {
      answer: 'I want a full refund.',
      status: 'answered',
    });

    const updated = res.data.clarifications.find((c) => c.id === 1);
    expect(updated?.status).toBe('answered');
    expect(updated?.answer).toBe('I want a full refund.');
  });

  it('patchDraft updates draft fields', async () => {
    const updatedDraft = {
      ...draftReady.data,
      draft: draftReady.data.draft
        ? { ...draftReady.data.draft, subject: 'Updated subject', body: 'Updated body text.' }
        : null,
    };

    mockFrom
      .mockReturnValueOnce({
        select: vi.fn(() => ({
          eq: vi.fn(() => ({
            single: vi.fn(() => Promise.resolve({ data: toDbRow(draftReady.data), error: null })),
          })),
        })),
      })
      .mockReturnValueOnce({
        update: vi.fn(() => ({
          eq: vi.fn(() => Promise.resolve({ error: null })),
        })),
      })
      .mockReturnValueOnce({
        update: vi.fn(() => ({
          eq: vi.fn(() => Promise.resolve({ error: null })),
        })),
      })
      .mockReturnValueOnce({
        select: vi.fn(() => ({
          eq: vi.fn(() => ({
            single: vi.fn(() => Promise.resolve({ data: toDbRow(updatedDraft), error: null })),
          })),
        })),
      });

    const res = await patchDraft(3, {
      subject: 'Updated subject',
      body: 'Updated body text.',
    });

    expect(res.data.draft?.subject).toBe('Updated subject');
    expect(res.data.draft?.body).toBe('Updated body text.');
    expect(res.data.draft?.language_code).toBe('en');
  });

  it('getCase response uses snake_case keys', async () => {
    mockQuery({ data: toDbRow(inputReady.data), error: null });

    const res = await getCase(1);
    const camelCaseKeys = Object.keys(res.data).filter((k) => /[A-Z]/.test(k));
    expect(camelCaseKeys).toHaveLength(0);
  });
});
