/**
 * Supabase data client — CRUD for cases, clarifications, and draft edits.
 * Web talks to Supabase directly for all non-voice/LLM operations.
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type {
  CaseClarification,
  CaseResponse,
  CreateCasePayload,
  PatchCasePayload,
  PatchClarificationPayload,
  PatchDraftPayload,
  SearchCasesData,
  SearchCasesResponse,
  SupportCase,
  SupportDraft,
} from './types.js';

const SUPABASE_URL = import.meta.env.PUBLIC_SUPABASE_URL as string | undefined;
const SUPABASE_ANON_KEY = import.meta.env.PUBLIC_SUPABASE_ANON_KEY as string | undefined;

const CLARIFICATION_FIELD_MAP: Record<
  CaseClarification['field_key'],
  'provider_name' | 'problem_summary' | 'desired_outcome'
> = {
  provider_name: 'provider_name',
  problem_summary: 'problem_summary',
  desired_outcome: 'desired_outcome',
};

function getClient(): SupabaseClient {
  if (!SUPABASE_URL) {
    throw new Error('PUBLIC_SUPABASE_URL is required');
  }
  if (!SUPABASE_ANON_KEY) {
    throw new Error('PUBLIC_SUPABASE_ANON_KEY is required');
  }
  return createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

function mapClarification(row: Record<string, unknown>): CaseClarification {
  return {
    id: Number(row.id),
    field_key: row.field_key as CaseClarification['field_key'],
    question: String(row.question),
    answer: (row.answer as string | null) ?? null,
    status: row.status as CaseClarification['status'],
    position: Number(row.position),
  };
}

function mapDraft(row: Record<string, unknown>): SupportDraft {
  return {
    id: Number(row.id),
    subject: String(row.subject),
    body: String(row.body),
    language_code: (row.language_code as string | null) ?? null,
  };
}

function mapCaseRow(row: Record<string, unknown>): SupportCase {
  const clarificationsRaw = (row.case_clarification as Record<string, unknown>[] | null) ?? [];
  const draftRaw = row.support_draft;
  const draftRow = Array.isArray(draftRaw) ? draftRaw[0] : draftRaw;

  return {
    id: Number(row.id),
    input_mode: row.input_mode as SupportCase['input_mode'],
    status: row.status as SupportCase['status'],
    case_text: (row.case_text as string | null) ?? null,
    language_code: (row.language_code as string | null) ?? null,
    provider_name: (row.provider_name as string | null) ?? null,
    service_name: (row.service_name as string | null) ?? null,
    issue_category: (row.issue_category as string | null) ?? null,
    problem_summary: (row.problem_summary as string | null) ?? null,
    attempted_resolutions: (row.attempted_resolutions as string[] | null) ?? [],
    desired_outcome: (row.desired_outcome as string | null) ?? null,
    support_email: (row.support_email as string | null) ?? null,
    support_phone: (row.support_phone as string | null) ?? null,
    support_url: (row.support_url as string | null) ?? null,
    clarifications: clarificationsRaw
      .map(mapClarification)
      .sort((a, b) => a.position - b.position),
    draft: draftRow ? mapDraft(draftRow as Record<string, unknown>) : null,
  };
}

const CASE_SELECT = '*, case_clarification(*), support_draft(*)';

function resolveStatus(caseData: SupportCase): SupportCase['status'] {
  const pending = caseData.clarifications.some((item) => item.status === 'pending');
  if (pending) return 'clarifying';
  const required = [caseData.provider_name, caseData.problem_summary, caseData.desired_outcome];
  if (required.every((value) => value && value.trim())) return 'ready_for_draft';
  return 'input_ready';
}

export async function createCase(payload: CreateCasePayload): Promise<CaseResponse> {
  const supabase = getClient();
  const insert = {
    input_mode: payload.input_mode,
    status: payload.input_mode === 'voice' ? 'transcribing' : 'input_ready',
    case_text: payload.case_text ?? null,
    provider_name: payload.provider_name ?? null,
  };

  const { data, error } = await supabase
    .from('support_case')
    .insert(insert)
    .select(CASE_SELECT)
    .single();

  if (error || !data) {
    throw new Error(error?.message ?? 'Failed to create case');
  }

  return { data: mapCaseRow(data as Record<string, unknown>) };
}

export async function getCase(caseId: number): Promise<CaseResponse> {
  const supabase = getClient();
  const { data, error } = await supabase
    .from('support_case')
    .select(CASE_SELECT)
    .eq('id', caseId)
    .single();

  if (error || !data) {
    throw new Error(error?.message ?? 'Case not found');
  }

  return { data: mapCaseRow(data as Record<string, unknown>) };
}

export async function patchCase(caseId: number, payload: PatchCasePayload): Promise<CaseResponse> {
  const supabase = getClient();
  const { data, error } = await supabase
    .from('support_case')
    .update(payload)
    .eq('id', caseId)
    .select(CASE_SELECT)
    .single();

  if (error || !data) {
    throw new Error(error?.message ?? 'Failed to update case');
  }

  return { data: mapCaseRow(data as Record<string, unknown>) };
}

export async function deleteCase(caseId: number): Promise<CaseResponse> {
  const existing = await getCase(caseId);
  const supabase = getClient();
  const { error } = await supabase.from('support_case').delete().eq('id', caseId);
  if (error) {
    throw new Error(error.message);
  }
  return existing;
}

export async function searchCases(payload: SearchCasesData = {}): Promise<SearchCasesResponse> {
  const supabase = getClient();
  let query = supabase.from('support_case').select(CASE_SELECT, { count: 'exact' });

  if (payload.query) {
    const term = `%${payload.query}%`;
    query = query.or(`case_text.ilike.${term},provider_name.ilike.${term}`);
  }

  const page = payload.page ?? 1;
  const limit = payload.limit ?? 10;
  const start = (page - 1) * limit;
  query = query.order('created_at', { ascending: false }).range(start, start + limit - 1);

  const { data, error, count } = await query;
  if (error) {
    throw new Error(error.message);
  }

  const cases = (data ?? []).map((row) => mapCaseRow(row as Record<string, unknown>));
  const total = count ?? cases.length;

  return {
    data: cases,
    total,
    page,
    next_page: start + limit < total ? page + 1 : undefined,
    previous_page: page > 1 ? page - 1 : undefined,
  };
}

export async function patchClarification(
  caseId: number,
  clarificationId: number,
  payload: PatchClarificationPayload,
): Promise<CaseResponse> {
  const current = await getCase(caseId);
  const clarification = current.data.clarifications.find((item) => item.id === clarificationId);
  if (!clarification) {
    throw new Error('Clarification not found');
  }

  const supabase = getClient();
  const { error: clarError } = await supabase
    .from('case_clarification')
    .update({
      status: payload.status,
      answer: payload.status === 'answered' ? payload.answer ?? null : null,
    })
    .eq('id', clarificationId);

  if (clarError) {
    throw new Error(clarError.message);
  }

  const caseUpdates: PatchCasePayload = {};
  if (payload.status === 'answered' && payload.answer) {
    const field = CLARIFICATION_FIELD_MAP[clarification.field_key];
    caseUpdates[field] = payload.answer.trim();
  }

  const reloaded = await getCase(caseId);
  const nextStatus = resolveStatus({
    ...reloaded.data,
    clarifications: reloaded.data.clarifications.map((item) =>
      item.id === clarificationId
        ? {
            ...item,
            status: payload.status,
            answer: payload.status === 'answered' ? payload.answer ?? null : null,
          }
        : item,
    ),
  });

  const { data, error } = await supabase
    .from('support_case')
    .update({ ...caseUpdates, status: nextStatus })
    .eq('id', caseId)
    .select(CASE_SELECT)
    .single();

  if (error || !data) {
    throw new Error(error?.message ?? 'Failed to update clarification');
  }

  return { data: mapCaseRow(data as Record<string, unknown>) };
}

export async function patchDraft(
  caseId: number,
  payload: PatchDraftPayload,
): Promise<CaseResponse> {
  const current = await getCase(caseId);
  if (!current.data.draft) {
    throw new Error('Draft not found');
  }

  const supabase = getClient();
  const { error: draftError } = await supabase
    .from('support_draft')
    .update(payload)
    .eq('case_id', caseId);

  if (draftError) {
    throw new Error(draftError.message);
  }

  const { error: caseError } = await supabase
    .from('support_case')
    .update({ status: 'draft_ready' })
    .eq('id', caseId);

  if (caseError) {
    throw new Error(caseError.message);
  }

  return getCase(caseId);
}
