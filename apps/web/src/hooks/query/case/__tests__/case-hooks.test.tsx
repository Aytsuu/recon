// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import {
  useCaseQuery,
  useSearchCasesQuery,
  useSearchCasesInfiniteQuery,
  useCreateCaseMutation,
  useUpdateCaseMutation,
  useDeleteCaseMutation,
  useExtractCaseMutation,
  useTranscribeCaseMutation,
  usePatchClarificationMutation,
  useGenerateDraftMutation,
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

    it('useExtractCaseMutation extracts case details', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useExtractCaseMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ caseId: 1 });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.status).toBe('clarifying');
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 1] });
    });

    it('useTranscribeCaseMutation transcribes audio', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useTranscribeCaseMutation(), {
        wrapper: createWrapper(),
      });

      const fakeAudio = new Blob(['audio data'], { type: 'audio/webm' });
      result.current.mutate({ caseId: 4, audio: fakeAudio });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.transcript).toBeDefined();
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

    it('useGenerateDraftMutation generates draft', async () => {
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
      const { result } = renderHook(() => useGenerateDraftMutation(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ caseId: 1 });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.data.status).toBe('draft_ready');
      expect(result.current.data?.data.draft).toBeDefined();
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['/cases', 1] });
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
