/** Query hook for platform health. */
import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../api/endpoints/health';
import { queryKeys } from './queryKeys';

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });
}
