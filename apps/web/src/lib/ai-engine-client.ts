/**
 * AI Engine client — voice token issuance and LLM processing only.
 * All other case operations go through supabase-client.ts.
 */

import type { CaseResponse } from './types.js';

const AI_ENGINE_URL = import.meta.env.PUBLIC_AI_ENGINE_URL as string | undefined;

export interface TranscriptionTokenData {
  case_id: number;
  token: string;
  expires_in_seconds: number;
  ws_url: string;
}

export interface TranscriptionTokenResponse {
  data: TranscriptionTokenData;
}

async function aiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!AI_ENGINE_URL) {
    throw new Error('PUBLIC_AI_ENGINE_URL is required');
  }

  const url = `${AI_ENGINE_URL}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`AI Engine ${init?.method ?? 'GET'} ${url} → ${res.status}: ${text}`);
  }

  return res.json() as Promise<T>;
}

export async function fetchTranscriptionToken(caseId: number): Promise<TranscriptionTokenResponse> {
  return aiFetch<TranscriptionTokenResponse>(`/api/cases/${caseId}/transcription-token`, {
    method: 'POST',
  });
}

export async function processVoice(caseId: number, caseText: string): Promise<CaseResponse> {
  return aiFetch<CaseResponse>(`/api/cases/${caseId}/process-voice`, {
    method: 'POST',
    body: JSON.stringify({ case_text: caseText }),
  });
}

export async function processCase(caseId: number): Promise<CaseResponse> {
  return aiFetch<CaseResponse>(`/api/cases/${caseId}/process`, {
    method: 'POST',
  });
}
