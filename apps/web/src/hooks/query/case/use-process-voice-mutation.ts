import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { processVoice, type CaseResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type ProcessVoiceVariables = {
  caseId: number;
  caseText: string;
};

export type UseProcessVoiceMutationArgs = MutationOptions<
  CaseResponse,
  Error,
  ProcessVoiceVariables
>;

export function useProcessVoiceMutation(args: UseProcessVoiceMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId, caseText }: ProcessVoiceVariables) =>
      processVoice(caseId, caseText),
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
