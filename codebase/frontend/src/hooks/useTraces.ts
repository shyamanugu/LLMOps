/** Query hooks for traces. */
import { useQuery } from '@tanstack/react-query';
import { fetchTrace, fetchTraces } from '../api/endpoints/traces';
import { queryKeys } from './queryKeys';

export function useTraces() {
  return useQuery({ queryKey: queryKeys.traces, queryFn: fetchTraces });
}

export function useTrace(id: string) {
  return useQuery({
    queryKey: queryKeys.trace(id),
    queryFn: () => fetchTrace(id),
    enabled: id.length > 0,
  });
}
