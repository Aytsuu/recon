import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { patchCase, type PatchCasePayload, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type UpdateCaseVariables = {
  caseId: number;
  payload: PatchCasePayload;
};

export type UseUpdateCaseMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  UpdateCaseVariables
>;

export function useUpdateCaseMutation(args: UseUpdateCaseMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId, payload }: UpdateCaseVariables) => patchCase(caseId, payload),
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
