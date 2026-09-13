import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { getCase, type CaseResponse, type GetCaseData } from '@/data';

export type UseCaseQueryArgs = GetCaseData &
  Omit<UseQueryOptions<CaseResponse, Error>, 'queryKey' | 'queryFn'>;

export function useCaseQuery(args: UseCaseQueryArgs) {
  const { caseId, ...options } = args;

  return useQuery({
    ...options,
    queryKey: ['/cases', caseId],
    queryFn: () => getCase(caseId),
  });
}
