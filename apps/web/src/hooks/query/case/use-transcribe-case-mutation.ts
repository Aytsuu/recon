import { type MutationOptions, useMutation, useQueryClient } from '@tanstack/react-query';
import { transcribeCase, type TranscribeResponse } from '@/data';
import { alertApiError } from '@/utils/api-errors';

export type TranscribeCaseVariables = {
  caseId: number;
  audio: Blob;
};

export type UseTranscribeCaseMutationArgs = MutationOptions<
  TranscribeResponse,
  Error,
  TranscribeCaseVariables
>;

export function useTranscribeCaseMutation(args: UseTranscribeCaseMutationArgs = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    ...args,
    mutationFn: ({ caseId, audio }: TranscribeCaseVariables) =>
      transcribeCase(caseId, audio),
    onSuccess: async (data, variables, context) => {
      await queryClient.invalidateQueries({ queryKey: ['/cases', variables.caseId] });
      args.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      if (args?.onError) return args.onError(error, variables, context);
      alertApiError(error);
    },
  });
}
