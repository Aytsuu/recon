/**
 * Shared TypeScript types for the RECON API contract.
 * All field names are snake_case to match FastAPI model and database column names.
 */

// ---------------------------------------------------------------------------
// Sub-entities
// ---------------------------------------------------------------------------

export interface CaseClarification {
  id: number;
  field_key: 'provider_name' | 'problem_summary' | 'desired_outcome';
  question: string;
  answer: string | null;
  status: 'pending' | 'answered' | 'skipped';
  position: number;
}

export interface SupportDraft {
  id: number;
  subject: string;
  body: string;
  language_code: string | null;
}

// ---------------------------------------------------------------------------
// Case
// ---------------------------------------------------------------------------

export type CaseStatus =
  | 'transcribing'
  | 'input_ready'
  | 'clarifying'
  | 'ready_for_draft'
  | 'draft_ready'
  | 'failed';

export type InputMode = 'typed' | 'voice';

export interface SupportCase {
  id: number;
  input_mode: InputMode;
  status: CaseStatus;
  case_text: string | null;
  language_code: string | null;
  provider_name: string | null;
  service_name: string | null;
  issue_category: string | null;
  problem_summary: string | null;
  attempted_resolutions: string[];
  desired_outcome: string | null;
  clarifications: CaseClarification[];
  draft: SupportDraft | null;
}

// ---------------------------------------------------------------------------
// API response envelopes
// ---------------------------------------------------------------------------

export interface CaseResponse {
  data: SupportCase;
}

export interface TranscribeResponse {
  data: {
    case_id: number;
    transcript: string;
    language_code: string | null;
  };
}

// ---------------------------------------------------------------------------
// Request payloads
// ---------------------------------------------------------------------------

export interface CreateCasePayload {
  input_mode: InputMode;
  case_text?: string;
  provider_name?: string;
}

export interface PatchCasePayload {
  case_text?: string;
  provider_name?: string;
  service_name?: string;
  problem_summary?: string;
  desired_outcome?: string;
  attempted_resolutions?: string[];
}

export interface PatchClarificationPayload {
  answer?: string;
  status: 'answered' | 'skipped';
}

export interface PatchDraftPayload {
  subject?: string;
  body?: string;
}

export interface GetCaseData {
  caseId: number;
}

export interface SearchCasesData {
  query?: string;
  page?: number;
  limit?: number;
  parentId?: string | number;
  [key: string]: unknown;
}

export interface SearchCasesResponse {
  data: SupportCase[];
  total: number;
  page: number;
  next_page?: number;
  previous_page?: number;
}

export type ApiError = Error;

