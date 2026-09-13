import {
  useInfiniteQuery,
  type InfiniteData,
  type UseInfiniteQueryOptions,
} from '@tanstack/react-query';
import { searchCases, type SearchCasesData, type SearchCasesResponse } from '@/data';

export type UseSearchCasesInfiniteQueryArgs = Omit<
  UseInfiniteQueryOptions<
    SearchCasesResponse,
    Error,
    InfiniteData<SearchCasesResponse>,
    SearchCasesResponse,
    readonly unknown[],
    number
  >,
  'queryKey' | 'queryFn' | 'initialPageParam' | 'getNextPageParam' | 'getPreviousPageParam'
> & {
  payload: SearchCasesData;
};

export function useSearchCasesInfiniteQuery({
  payload,
  ...options
}: UseSearchCasesInfiniteQueryArgs) {
  return useInfiniteQuery({
    ...options,
    queryKey: ['/cases', '/search', '/infinite', payload.parentId, { ...payload }] as const,
    queryFn: ({ pageParam }) => searchCases({ ...payload, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.next_page,
    getPreviousPageParam: (firstPage) => firstPage.previous_page,
  });
}
