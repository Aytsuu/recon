import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { createCase, type CreateCasePayload, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type UseCreateCaseMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  CreateCasePayload
>;

export function useCreateCaseMutation(args: UseCreateCaseMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: createCase,
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
