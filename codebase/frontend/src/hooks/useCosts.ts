/** Query hook for cost aggregates. */
import { useQuery } from '@tanstack/react-query';
import { fetchCosts } from '../api/endpoints/costs';
import { queryKeys } from './queryKeys';

export function useCosts(windowDays = 7) {
  return useQuery({
    queryKey: queryKeys.costs(windowDays),
    queryFn: () => fetchCosts(windowDays),
  });
}
