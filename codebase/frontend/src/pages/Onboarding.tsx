/** Onboarding: a new-use-case checklist mirroring the platform onboarding steps. */
import { useMemo, useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { Badge } from '../components/MetricBadge';
import { useUsecases } from '../hooks/useUsecases';
import { ONBOARDING_STEPS } from '../api/endpoints/usecases';
import type { OnboardingStep, OnboardingStepStatus, UseCase } from '../api/types';

const MARKER: Record<OnboardingStepStatus, string> = {
  done: '✓',
  in_progress: '•',
  pending: '',
};

function Checklist({ steps }: { steps: OnboardingStep[] }): JSX.Element {
  return (
    <div className="checklist">
      {steps.map((step, i) => (
        <div key={step.key} className="checklist__item">
          <div
            className={`checklist__marker${step.status === 'done' ? ' is-done' : ''}${
              step.status === 'in_progress' ? ' is-active' : ''
            }`}
            aria-hidden="true"
          >
            {step.status === 'pending' ? i + 1 : MARKER[step.status]}
          </div>
          <div className="checklist__body">
            <h3>
              {step.title}{' '}
              {step.status === 'in_progress' ? <Badge tone="info">in progress</Badge> : null}
              {step.status === 'done' ? <Badge tone="success">done</Badge> : null}
            </h3>
            <p>{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function UseCasePicker({ usecases }: { usecases: UseCase[] }): JSX.Element {
  const [slug, setSlug] = useState<string>(usecases[0]?.slug ?? '');
  const selected = useMemo(
    () => usecases.find((u) => u.slug === slug) ?? usecases[0],
    [usecases, slug],
  );

  const template: OnboardingStep[] = ONBOARDING_STEPS.map((s) => ({ ...s, status: 'pending' }));

  return (
    <div className="stack">
      <section className="card">
        <div className="card__header">
          <h2 className="card__title">Use case progress</h2>
          <label className="topbar__env">
            <span className="field__label">Use case</span>
            <select value={slug} onChange={(e) => setSlug(e.target.value)}>
              {usecases.map((u) => (
                <option key={u.slug} value={u.slug}>
                  {u.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="card__body">
          {selected ? (
            <>
              <div className="row" style={{ marginBottom: 12, flexWrap: 'wrap' }}>
                <Badge tone={selected.status === 'active' ? 'success' : 'warning'}>
                  {selected.status}
                </Badge>
                <Badge tone="info">{selected.environment}</Badge>
                {selected.owner ? <span className="muted">owner: {selected.owner}</span> : null}
              </div>
              <Checklist steps={selected.steps} />
            </>
          ) : null}
        </div>
      </section>

      <section className="card">
        <div className="card__header">
          <h2 className="card__title">New use-case checklist</h2>
        </div>
        <div className="card__body">
          <p className="muted">
            Every new use case follows these ten steps from scaffold to production. Start by copying
            <span className="mono"> usecases/_template</span> and work down the list.
          </p>
          <Checklist steps={template} />
        </div>
      </section>
    </div>
  );
}

export function Onboarding(): JSX.Element {
  const query = useUsecases();
  return (
    <>
      <PageHeader
        title="Onboarding"
        subtitle="Bring a new use case onto the platform with a repeatable, gated checklist."
      />
      <AsyncSection query={query} loadingLabel="Loading use cases…">
        {(usecases) => <UseCasePicker usecases={usecases} />}
      </AsyncSection>
    </>
  );
}
