/** Query hook for the model catalog. */
import { useQuery } from '@tanstack/react-query';
import { fetchModels } from '../api/endpoints/models';
import type { Environment } from '../api/types';
import { queryKeys } from './queryKeys';

export function useModels(env: Environment) {
  return useQuery({
    queryKey: queryKeys.models(env),
    queryFn: () => fetchModels(env),
  });
}
