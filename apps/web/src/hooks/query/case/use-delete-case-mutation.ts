import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteCase, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type DeleteCaseVariables = {
  caseId: number;
};

export type UseDeleteCaseMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  DeleteCaseVariables
>;

export function useDeleteCaseMutation(args: UseDeleteCaseMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId }: DeleteCaseVariables) => deleteCase(caseId),
    onSuccess: async (data, variables, context) => {
      await queryClient.invalidateQueries({ queryKey: ['/cases'] });
      args.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      if (args?.onError) return args.onError(error, variables, context);
      alertApiError(error);
    },
  });
}
