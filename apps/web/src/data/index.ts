/**
 * Data access layer for RECON entities.
 */

export {
  createCase,
  getCase,
  patchCase,
  deleteCase,
  searchCases,
  patchClarification,
  patchDraft,
} from '../lib/supabase-client.js';

export {
  fetchTranscriptionToken,
  processVoice,
  processCase,
} from '../lib/ai-engine-client.js';

export type {
  CaseClarification,
  SupportDraft,
  CaseStatus,
  InputMode,
  SupportCase,
  CaseResponse,
  CreateCasePayload,
  PatchCasePayload,
  PatchClarificationPayload,
  PatchDraftPayload,
  GetCaseData,
  SearchCasesData,
  SearchCasesResponse,
  ApiError,
} from '../lib/types.js';

export type {
  TranscriptionTokenData,
  TranscriptionTokenResponse,
} from '../lib/ai-engine-client.js';
