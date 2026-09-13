/**
 * API client unit tests
 *
 * These tests run entirely against the shared JSON fixtures in
 * src/fixtures/cases.json and do not require a running FastAPI server.
 *
 * Mock mode is forced via import.meta.env stub injected by vitest config.
 *
 * Run:
 *   npx vitest run src/lib/__tests__/api-client.test.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Stub import.meta.env before importing the client so the module sees mock mode.
vi.stubGlobal('import', {
  meta: {
    env: {
      PUBLIC_API_MODE: 'mock',
      PUBLIC_API_BASE_URL: 'http://127.0.0.1:8000',
    },
  },
});

// Dynamic import after env is stubbed
const clientModule = await import('../api-client.js');
const {
  createCase,
  getCase,
  patchCase,
  extractCase,
  generateDraft,
  patchClarification,
  patchDraft,
} = clientModule;

// ---------------------------------------------------------------------------
// Fixtures reference
// ---------------------------------------------------------------------------
import FIXTURES from '../../fixtures/cases.json';

const inputReady  = FIXTURES.input_ready_typed.data;
const clarifying  = FIXTURES.clarifying_typed.data;
const draftReady  = FIXTURES.draft_ready_typed.data;

// ---------------------------------------------------------------------------
// createCase
// ---------------------------------------------------------------------------
describe('createCase (mock)', () => {
  it('returns an input_ready typed case for typed input_mode', async () => {
    const res = await createCase({ input_mode: 'typed', case_text: 'My internet is broken.' });
    expect(res.data.input_mode).toBe('typed');
    expect(res.data.status).toBe('input_ready');
    expect(typeof res.data.id).toBe('number');
  });

  it('returns a transcribing voice case for voice input_mode', async () => {
    const res = await createCase({ input_mode: 'voice' });
    expect(res.data.input_mode).toBe('voice');
    expect(res.data.status).toBe('transcribing');
  });

  it('assigns a unique id to each new mock case', async () => {
    const r1 = await createCase({ input_mode: 'typed' });
    const r2 = await createCase({ input_mode: 'typed' });
    expect(r1.data.id).not.toBe(r2.data.id);
  });
});

// ---------------------------------------------------------------------------
// getCase
// ---------------------------------------------------------------------------
describe('getCase (mock)', () => {
  it('returns the input_ready fixture for id=1', async () => {
    const res = await getCase(1);
    expect(res.data).toMatchObject({ id: inputReady.id, status: 'input_ready' });
  });

  it('returns the clarifying fixture for id=2', async () => {
    const res = await getCase(2);
    expect(res.data.status).toBe('clarifying');
    expect(res.data.clarifications).toHaveLength(1);
  });

  it('returns the draft_ready fixture for id=3', async () => {
    const res = await getCase(3);
    expect(res.data.status).toBe('draft_ready');
    expect(res.data.draft).not.toBeNull();
    expect(res.data.draft?.subject).toBeTruthy();
  });

  it('returns a case with a non-null draft for id=3', async () => {
    const res = await getCase(3);
    expect(res.data.draft).toHaveProperty('id');
    expect(res.data.draft).toHaveProperty('body');
  });
});

// ---------------------------------------------------------------------------
// patchCase
// ---------------------------------------------------------------------------
describe('patchCase (mock)', () => {
  it('merges the patch payload into the base fixture', async () => {
    const res = await patchCase(1, { case_text: 'Updated problem text' });
    expect(res.data.case_text).toBe('Updated problem text');
    expect(res.data.id).toBe(inputReady.id);
  });

  it('preserves unpatched fields', async () => {
    const res = await patchCase(1, { provider_name: 'Globe' });
    expect(res.data.status).toBe(inputReady.status);
  });
});

// ---------------------------------------------------------------------------
// extractCase
// ---------------------------------------------------------------------------
describe('extractCase (mock)', () => {
  it('returns the clarifying fixture', async () => {
    const res = await extractCase(1);
    expect(res.data.status).toBe('clarifying');
    expect(res.data.clarifications.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// patchClarification
// ---------------------------------------------------------------------------
describe('patchClarification (mock)', () => {
  it('marks a clarification as answered', async () => {
    const res = await patchClarification(2, 1, {
      answer: 'I want a full refund.',
      status: 'answered',
    });
    const updated = res.data.clarifications.find((c) => c.id === 1);
    expect(updated?.status).toBe('answered');
    expect(updated?.answer).toBe('I want a full refund.');
  });

  it('marks a clarification as skipped', async () => {
    const res = await patchClarification(2, 1, { status: 'skipped' });
    const updated = res.data.clarifications.find((c) => c.id === 1);
    expect(updated?.status).toBe('skipped');
  });
});

// ---------------------------------------------------------------------------
// generateDraft
// ---------------------------------------------------------------------------
describe('generateDraft (mock)', () => {
  it('returns the draft_ready fixture with a non-null draft', async () => {
    const res = await generateDraft(1);
    expect(res.data.status).toBe('draft_ready');
    expect(res.data.draft).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// patchDraft
// ---------------------------------------------------------------------------
describe('patchDraft (mock)', () => {
  it('merges subject and body edits into the draft', async () => {
    const res = await patchDraft(3, {
      subject: 'Updated subject',
      body: 'Updated body text.',
    });
    expect(res.data.draft?.subject).toBe('Updated subject');
    expect(res.data.draft?.body).toBe('Updated body text.');
  });

  it('preserves unchanged draft fields', async () => {
    const res = await patchDraft(3, { subject: 'New subject' });
    expect(res.data.draft?.language_code).toBe(draftReady.draft?.language_code);
  });
});

// ---------------------------------------------------------------------------
// Field shape – no translation layer needed
// ---------------------------------------------------------------------------
describe('snake_case field contract', () => {
  it('getCase response uses only snake_case keys at data level', async () => {
    const res = await getCase(1);
    const keys = Object.keys(res.data);
    const camelCaseKeys = keys.filter((k) => /[A-Z]/.test(k));
    expect(camelCaseKeys).toHaveLength(0);
  });

  it('clarification objects use only snake_case keys', async () => {
    const res = await getCase(2);
    for (const c of res.data.clarifications) {
      const camelKeys = Object.keys(c).filter((k) => /[A-Z]/.test(k));
      expect(camelKeys).toHaveLength(0);
    }
  });

  it('draft object uses only snake_case keys', async () => {
    const res = await getCase(3);
    if (res.data.draft) {
      const camelKeys = Object.keys(res.data.draft).filter((k) => /[A-Z]/.test(k));
      expect(camelKeys).toHaveLength(0);
    }
  });
});
