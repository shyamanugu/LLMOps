/** Query hooks for the prompt registry. */
import { useMutation, useQuery } from '@tanstack/react-query';
import { fetchPrompt, fetchPrompts, renderPrompt } from '../api/endpoints/prompts';
import type { JsonValue } from '../api/types';
import { queryKeys } from './queryKeys';

export function usePrompts() {
  return useQuery({ queryKey: queryKeys.prompts, queryFn: fetchPrompts });
}

export function usePrompt(id: string) {
  return useQuery({
    queryKey: queryKeys.prompt(id),
    queryFn: () => fetchPrompt(id),
    enabled: id.length > 0,
  });
}

export function useRenderPrompt(id: string) {
  return useMutation({
    mutationFn: (vars: Record<string, JsonValue>) => renderPrompt(id, vars),
  });
}
