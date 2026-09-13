import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { patchClarification, type PatchClarificationPayload, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type PatchClarificationVariables = {
  caseId: number;
  clarificationId: number;
  payload: PatchClarificationPayload;
};

export type UsePatchClarificationMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  PatchClarificationVariables
>;

export function usePatchClarificationMutation(
  args: UsePatchClarificationMutationArgs = {},
) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId, clarificationId, payload }: PatchClarificationVariables) =>
      patchClarification(caseId, clarificationId, payload),
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
