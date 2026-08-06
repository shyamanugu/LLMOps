/** Query hook for guardrails config + events. */
import { useQuery } from '@tanstack/react-query';
import { fetchGuardrails } from '../api/endpoints/guardrails';
import { queryKeys } from './queryKeys';

export function useGuardrails() {
  return useQuery({ queryKey: queryKeys.guardrails, queryFn: fetchGuardrails });
}
