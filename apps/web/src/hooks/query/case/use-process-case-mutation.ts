import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { processCase, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type ProcessCaseVariables = {
  caseId: number;
};

export type UseProcessCaseMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  ProcessCaseVariables
>;

export function useProcessCaseMutation(args: UseProcessCaseMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId }: ProcessCaseVariables) => processCase(caseId),
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
