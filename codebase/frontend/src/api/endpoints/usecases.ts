/** Use cases / onboarding endpoint (GET /usecases). */
import { getJson, withPlaceholder, type Resulted } from '../client';
import type { OnboardingStep, UseCase } from '../types';

/** The canonical platform onboarding steps, mirrored by the Onboarding page. */
export const ONBOARDING_STEPS: ReadonlyArray<Omit<OnboardingStep, 'status'>> = [
  { key: 'scaffold', title: 'Scaffold from template', description: 'Copy usecases/_template into usecases/<slug> and set metadata.' },
  { key: 'prompts', title: 'Author prompts', description: 'Add .prompt.yaml files with inputs, template and eval_refs.' },
  { key: 'models', title: 'Bind model aliases', description: 'Choose reason/bulk/judge aliases per platform/models.yaml.' },
  { key: 'data', title: 'Wire data access', description: 'Configure RAG index, SQL tables or document extractors.' },
  { key: 'tools', title: 'Register tools', description: 'Select MCP tools from platform/tools/registry.yaml.' },
  { key: 'pipeline', title: 'Define pipeline', description: 'Compose agents into agents/pipeline.agent.yaml (sequential).' },
  { key: 'guardrails', title: 'Enable guardrails', description: 'Turn on injection, content safety, PII and schema guards.' },
  { key: 'golden', title: 'Add golden set', description: 'Provide golden cases and grading for the evaluation gate.' },
  { key: 'gate', title: 'Pass the eval gate', description: 'Run evals; meet absolute floors and baseline-relative thresholds.' },
  { key: 'deploy', title: 'Deploy & observe', description: 'Ship via CI/CD and confirm traces, cost and feedback flow.' },
];

function buildSteps(doneCount: number, activeIndex: number): OnboardingStep[] {
  return ONBOARDING_STEPS.map((step, i) => ({
    ...step,
    status: i < doneCount ? 'done' : i === activeIndex ? 'in_progress' : 'pending',
  }));
}

function placeholder(): UseCase[] {
  return [
    {
      slug: 'apix',
      name: 'APIX Support Triage',
      description: 'Automated support ticket triage and summarisation.',
      environment: 'prod',
      status: 'active',
      owner: 'platform-team',
      steps: buildSteps(10, 10),
    },
    {
      slug: 'hiring',
      name: 'Hiring Screen',
      description: 'Resume screening against job descriptions with bias checks.',
      environment: 'test',
      status: 'onboarding',
      owner: 'talent-eng',
      steps: buildSteps(7, 7),
    },
  ];
}

/** Fetch onboarded use cases and their onboarding status. */
export function fetchUseCases(): Promise<Resulted<UseCase[]>> {
  return withPlaceholder(() => getJson<UseCase[]>('/usecases'), placeholder);
}
