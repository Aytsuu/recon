import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { patchDraft, type PatchDraftPayload, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type PatchDraftVariables = {
  caseId: number;
  payload: PatchDraftPayload;
};

export type UsePatchDraftMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  PatchDraftVariables
>;

export function usePatchDraftMutation(args: UsePatchDraftMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId, payload }: PatchDraftVariables) => patchDraft(caseId, payload),
    onSuccess: async (data, variables, context) => {
      await queryClient.invalidateQueries({ queryKey: ['/cases'] });
      await queryClient.invalidateQueries({ queryKey: ['/cases', variables.caseId] });
      args.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      if (args?.onError) return args.onError(error, variables, context);
      alertApiError(error);
    },
  });
}
