// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { CaseResponse, SearchCasesResponse } from '@/data';

const inputReady: CaseResponse = {
  data: {
    id: 1,
    input_mode: 'typed',
    status: 'input_ready',
    case_text: 'My internet keeps disconnecting.',
    language_code: 'en',
    provider_name: 'Converge ICT',
    service_name: null,
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
    case_text: 'Unexpected bill charges.',
    language_code: 'en',
    provider_name: 'Globe Telecom',
    service_name: null,
    issue_category: 'billing',
    problem_summary: 'Unexpected charges.',
    attempted_resolutions: [],
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
    case_text: 'Fiber drops for three days.',
    language_code: 'en',
    provider_name: 'PLDT Home',
    service_name: null,
    issue_category: null,
    problem_summary: 'Connection drops.',
    attempted_resolutions: [],
    desired_outcome: 'Technician dispatch.',
    support_email: null,
    support_phone: null,
    support_url: null,
    clarifications: [],
    draft: {
      id: 1,
      subject: 'Fiber issue',
      body: 'Dear support...',
      language_code: 'en',
    },
  },
};

const searchResponse: SearchCasesResponse = {
  data: [inputReady.data, clarifying.data, draftReady.data],
  total: 3,
  page: 1,
};

const {
  getCase,
  searchCases,
  createCase,
  patchCase,
  deleteCase,
  processCase,
  processVoice,
  patchClarification,
  patchDraft,
} = vi.hoisted(() => ({
  getCase: vi.fn(),
  searchCases: vi.fn(),
  createCase: vi.fn(),
  patchCase: vi.fn(),
  deleteCase: vi.fn(),
  processCase: vi.fn(),
  processVoice: vi.fn(),
  patchClarification: vi.fn(),
  patchDraft: vi.fn(),
}));

vi.mock('@/data', () => ({
  getCase,
  searchCases,
  createCase,
  patchCase,
  deleteCase,
  processCase,
  processVoice,
  patchClarification,
  patchDraft,
}));

import {
  useCaseQuery,
  useSearchCasesQuery,
  useSearchCasesInfiniteQuery,
  useCreateCaseMutation,
  useUpdateCaseMutation,
  useDeleteCaseMutation,
  useProcessCaseMutation,
  useProcessVoiceMutation,
  usePatchClarificationMutation,
  usePatchDraftMutation,
} from '../index.js';

describe('Case Query & Mutation Hooks', () => {
  let queryClient: QueryClient;

  function createWrapper() {
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children);
  }

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    vi.clearAllMocks();

    getCase.mockImplementation(async (caseId: number) => {
      if (caseId === 1) return inputReady;
      if (caseId === 2) return clarifying;
      if (caseId === 3) return draftReady;
      return inputReady;
    });

    searchCases.mockImplementation(async (payload: { query?: string; page?: number; limit?: number } = {}) => {
      const filtered = payload.query
        ? searchResponse.data.filter(
            (c) =>
              c.case_text?.toLowerCase().includes(payload.query!.toLowerCase()) ||
              c.provider_name?.toLowerCase().includes(payload.query!.toLowerCase()),
          )
        : searchResponse.data;

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
    });

    createCase.mockImplementation(async (payload: { input_mode: string; case_text?: string }) => ({
      data: {
        ...inputReady.data,
        id: 99,
        input_mode: payload.input_mode as 'typed' | 'voice',
        case_text: payload.case_text ?? null,
        status: payload.input_mode === 'voice' ? 'transcribing' : 'input_ready',
      },
    }));

    patchCase.mockImplementation(async (caseId: number, payload: Record<string, unknown>) => ({
      data: { ...inputReady.data, id: caseId, ...payload },
    }));

    deleteCase.mockResolvedValue(inputReady);

    processCase.mockResolvedValue({
      data: { ...clarifying.data, status: 'clarifying' },
    });

    processVoice.mockResolvedValue(draftReady);

    patchClarification.mockImplementation(
      async (caseId: number, clarificationId: number, payload: { answer?: string; status: string }) => ({
        data: {
          ...clarifying.data,
          id: caseId,
          clarifications: clarifying.data.clarifications.map((c) =>
            c.id === clarificationId ? { ...c, ...payload } : c,
          ),
        },
      }),
    );

    patchDraft.mockImplementation(async (caseId: number, payload: { subject?: string; body?: string }) => ({
      data: {
        ...draftReady.data,
        id: caseId,
        draft: draftReady.data.draft ? { ...draftReady.data.draft, ...payload } : null,
      },
    }));
  });

  describe('Query Hooks', () => {
    it('useCaseQuery fetches a case by ID', async () => {
      const { result } = renderHook(() => useCaseQuery({ caseId: 1 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.id).toBe(1);
      expect(result.current.data?.data.status).toBe('input_ready');
    });

    it('useSearchCasesQuery searches cases with payload', async () => {
      const { result } = renderHook(
        () => useSearchCasesQuery({ payload: { query: 'internet' } }),
        { wrapper: createWrapper() },
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data).toBeDefined();
      expect(Array.isArray(result.current.data?.data)).toBe(true);
      expect(result.current.data?.total).toBeGreaterThan(0);
    });

    it('useSearchCasesInfiniteQuery handles infinite pagination', async () => {
      const { result } = renderHook(
        () => useSearchCasesInfiniteQuery({ payload: { limit: 2 } }),
        { wrapper: createWrapper() },
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.pages[0].data).toBeDefined();
      expect(result.current.data?.pages[0].page).toBe(1);
    });
  });

  describe('Mutation Hooks', () => {
    it('useCreateCaseMutation creates a case and invalidates queries', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useCreateCaseMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ input_mode: 'typed', case_text: 'Test problem' });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.input_mode).toBe('typed');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
    });

    it('useUpdateCaseMutation updates a case and invalidates case query', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useUpdateCaseMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ caseId: 1, payload: { provider_name: 'PLDT' } });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.provider_name).toBe('PLDT');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 1] });
    });

    it('useDeleteCaseMutation deletes a case', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useDeleteCaseMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ caseId: 1 });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
    });

    it('useProcessCaseMutation processes a case', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useProcessCaseMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ caseId: 1 });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.status).toBe('clarifying');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 1] });
    });

    it('useProcessVoiceMutation processes voice transcript', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useProcessVoiceMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ caseId: 4, caseText: 'My internet is down.' });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.status).toBe('draft_ready');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 4] });
    });

    it('usePatchClarificationMutation answers clarification question', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => usePatchClarificationMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        caseId: 2,
        clarificationId: 1,
        payload: { answer: 'Converge ICT', status: 'answered' },
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.clarifications[0].status).toBe('answered');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 2] });
    });

    it('usePatchDraftMutation updates draft content', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => usePatchDraftMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        caseId: 3,
        payload: { subject: 'Custom Subject', body: 'Custom Body' },
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.draft?.subject).toBe('Custom Subject');
      expect(result.current.data?.data.draft?.body).toBe('Custom Body');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 3] });
    });
  });
});
