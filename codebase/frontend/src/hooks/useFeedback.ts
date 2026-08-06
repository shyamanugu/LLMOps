/** Query + mutation hooks for feedback. */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { captureFeedback, fetchFeedback } from '../api/endpoints/feedback';
import type { FeedbackCreate } from '../api/types';
import { queryKeys } from './queryKeys';

export function useFeedback() {
  return useQuery({ queryKey: queryKeys.feedback, queryFn: fetchFeedback });
}

export function useCaptureFeedback() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: FeedbackCreate) => captureFeedback(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.feedback });
    },
  });
}
