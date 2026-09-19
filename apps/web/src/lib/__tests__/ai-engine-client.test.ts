/**
 * AI Engine client unit tests — mocks fetch, no shared fixtures.
 *
 * Run:
 *   npx vitest run src/lib/__tests__/ai-engine-client.test.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { CaseResponse } from '../types.js';

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
    attempted_resolutions: ['Restarted the ONT'],
    desired_outcome: 'Restore stable connection.',
    support_email: 'support@example.com',
    support_phone: null,
    support_url: null,
    clarifications: [],
    draft: {
      id: 1,
      subject: 'Fiber connection issue',
      body: 'Dear support...',
      language_code: 'en',
    },
  },
};

vi.stubEnv('PUBLIC_AI_ENGINE_URL', 'http://127.0.0.1:8000');

const { fetchTranscriptionToken, processVoice, processCase } = await import('../ai-engine-client.js');

describe('ai-engine-client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetchTranscriptionToken posts to the token endpoint', async () => {
    const tokenResponse = {
      data: {
        case_id: 4,
        token: 'test-token',
        expires_in_seconds: 60,
        ws_url: 'wss://streaming.assemblyai.com/v3/ws',
      },
    };

    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(tokenResponse),
        }),
      ),
    );

    const res = await fetchTranscriptionToken(4);
    expect(res.data.token).toBe('test-token');
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/cases/4/transcription-token',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('processVoice posts case_text to process-voice', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(draftReady),
        }),
      ),
    );

    const res = await processVoice(4, 'My internet is down.');
    expect(res.data.status).toBe('draft_ready');
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/cases/4/process-voice',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ case_text: 'My internet is down.' }),
      }),
    );
  });

  it('processCase posts to the process endpoint', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(draftReady),
        }),
      ),
    );

    const res = await processCase(1);
    expect(res.data.draft).not.toBeNull();
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/cases/1/process',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('throws when AI Engine returns a non-OK response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
          text: () => Promise.resolve('processing failed'),
        }),
      ),
    );

    await expect(processCase(1)).rejects.toThrow(/500/);
  });
});
