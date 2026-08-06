/** Centralised React Query cache keys, one namespace per resource. */
export const queryKeys = {
  health: ['health'] as const,
  prompts: ['prompts'] as const,
  prompt: (id: string) => ['prompts', id] as const,
  models: (env: string) => ['models', env] as const,
  evaluations: ['evaluations'] as const,
  traces: ['traces'] as const,
  trace: (id: string) => ['traces', id] as const,
  costs: (windowDays: number) => ['costs', windowDays] as const,
  feedback: ['feedback'] as const,
  agents: ['agents'] as const,
  guardrails: ['guardrails'] as const,
  usecases: ['usecases'] as const,
} as const;
