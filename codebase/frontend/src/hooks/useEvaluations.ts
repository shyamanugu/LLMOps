/** Query + mutation hooks for the evaluation gate. */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchEvaluations, runEvaluation } from '../api/endpoints/evaluations';
import type { EvaluationRunRequest } from '../api/types';
import { queryKeys } from './queryKeys';

export function useEvaluations() {
  return useQuery({ queryKey: queryKeys.evaluations, queryFn: fetchEvaluations });
}

export function useRunEvaluation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (req: EvaluationRunRequest) => runEvaluation(req),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.evaluations });
    },
  });
}
