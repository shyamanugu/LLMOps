/** Query hook for pipelines/agents. */
import { useQuery } from '@tanstack/react-query';
import { fetchAgents } from '../api/endpoints/agents';
import { queryKeys } from './queryKeys';

export function useAgents() {
  return useQuery({ queryKey: queryKeys.agents, queryFn: fetchAgents });
}
