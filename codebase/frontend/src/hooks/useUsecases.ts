/** Query hook for onboarded use cases. */
import { useQuery } from '@tanstack/react-query';
import { fetchUseCases } from '../api/endpoints/usecases';
import { queryKeys } from './queryKeys';

export function useUsecases() {
  return useQuery({ queryKey: queryKeys.usecases, queryFn: fetchUseCases });
}
