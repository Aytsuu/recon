import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { generateDraft, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type GenerateDraftVariables = {
  caseId: number;
};

export type UseGenerateDraftMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  GenerateDraftVariables
>;

export function useGenerateDraftMutation(args: UseGenerateDraftMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId }: GenerateDraftVariables) => generateDraft(caseId),
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
