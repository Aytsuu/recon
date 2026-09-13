import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { type ApiError, searchCases, type SearchCasesData, type SearchCasesResponse } from '@/data';

export type UseSearchCasesQueryArgs = Omit<
  UseQueryOptions<SearchCasesResponse, ApiError>,
  'queryKey' | 'queryFn'
> & {
  payload: SearchCasesData;
};

export function useSearchCasesQuery({ payload, ...args }: UseSearchCasesQueryArgs) {
  return useQuery({
    ...args,
    queryKey: ['/cases', '/search', payload],
    queryFn: () => searchCases(payload),
  });
}
