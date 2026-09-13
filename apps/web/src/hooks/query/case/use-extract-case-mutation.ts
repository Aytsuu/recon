import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { extractCase, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type ExtractCaseVariables = {
  caseId: number;
};

export type UseExtractCaseMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  ExtractCaseVariables
>;

export function useExtractCaseMutation(args: UseExtractCaseMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId }: ExtractCaseVariables) => extractCase(caseId),
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
