/**
 * Data access layer for RECON entities.
 * Re-exports API functions and types for consumption by TanStack Query hooks,
 * server components, or UI boundaries.
 */

export {
  createCase,
  getCase,
  patchCase,
  deleteCase,
  transcribeCase,
  extractCase,
  patchClarification,
  generateDraft,
  patchDraft,
  searchCases,
} from '../lib/api-client.js';

export type {
  CaseClarification,
  SupportDraft,
  CaseStatus,
  InputMode,
  SupportCase,
  CaseResponse,
  TranscribeResponse,
  CreateCasePayload,
  PatchCasePayload,
  PatchClarificationPayload,
  PatchDraftPayload,
  GetCaseData,
  SearchCasesData,
  SearchCasesResponse,
  ApiError,
} from '../lib/types.js';
