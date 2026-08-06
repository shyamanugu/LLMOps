/** Prompt detail with a version-compare view. */
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { CodeBlock } from '../components/CodeBlock';
import { Badge } from '../components/MetricBadge';
import { PlaceholderBanner } from '../components/PlaceholderBanner';
import { usePrompt } from '../hooks/usePrompts';
import type { PromptSpec } from '../api/types';

/** Reconstruct an illustrative earlier version from the changelog. */
function versionView(spec: PromptSpec, version: number): {
  version: number;
  changelog: string;
  isCurrent: boolean;
} {
  const isCurrent = version === spec.version;
  const idx = spec.version - version;
  const changelog = spec.changelog[idx] ?? `v${version}: (history not in registry cache)`;
  return { version, changelog, isCurrent };
}

function CompareColumn({
  spec,
  version,
}: {
  spec: PromptSpec;
  version: number;
}): JSX.Element {
  const view = versionView(spec, version);
  return (
    <div className="compare__col">
      <h3>
        v{view.version} {view.isCurrent ? <Badge tone="success">current</Badge> : <Badge>historical</Badge>}
      </h3>
      <div className="field">
        <div className="field__label">Changelog</div>
        <div>{view.changelog}</div>
      </div>
      <div className="field">
        <div className="field__label">Model alias · temperature</div>
        <div>
          <Badge tone="info">{spec.model_alias}</Badge>{' '}
          <span className="mono">{spec.temperature}</span>
        </div>
      </div>
      <div className="field">
        <div className="field__label">Template</div>
        {view.isCurrent ? (
          <CodeBlock code={spec.template} language="jinja" />
        ) : (
          <p className="muted">
            Historical template bodies are served by the prompt registry; not cached here.
          </p>
        )}
      </div>
    </div>
  );
}

export function PromptDetail(): JSX.Element {
  const { id = '' } = useParams();
  const query = usePrompt(id);

  return (
    <>
      <PageHeader
        title={id}
        subtitle="Prompt spec and version comparison."
        actions={
          <Link to="/prompts" className="btn btn--secondary btn--sm">
            Back to prompts
          </Link>
        }
      />
      <AsyncSection query={query}>
        {(spec) => <PromptDetailBody spec={spec} />}
      </AsyncSection>
    </>
  );
}

function PromptDetailBody({ spec }: { spec: PromptSpec }): JSX.Element {
  const versions = useMemo(
    () => Array.from({ length: spec.version }, (_, i) => spec.version - i),
    [spec.version],
  );
  const [left, setLeft] = useState<number>(Math.max(1, spec.version - 1));
  const [right, setRight] = useState<number>(spec.version);

  return (
    <div className="stack">
      <section className="card">
        <div className="card__header">
          <h2 className="card__title">Overview</h2>
          <span className="chip-row">
            {spec.labels.map((l) => (
              <Badge key={l}>{l}</Badge>
            ))}
          </span>
        </div>
        <div className="card__body stack">
          <div className="row" style={{ flexWrap: 'wrap', gap: 24 }}>
            <span>
              <span className="field__label">Current version</span>
              <div className="mono">v{spec.version}</div>
            </span>
            <span>
              <span className="field__label">Inputs</span>
              <div className="chip-row">
                {spec.inputs.map((i) => (
                  <Badge key={i} tone="neutral">
                    {i}
                  </Badge>
                ))}
              </div>
            </span>
            <span>
              <span className="field__label">Eval refs</span>
              <div className="chip-row">
                {spec.eval_refs.length > 0 ? (
                  spec.eval_refs.map((r) => (
                    <Badge key={r} tone="info">
                      {r}
                    </Badge>
                  ))
                ) : (
                  <span className="muted">none</span>
                )}
              </div>
            </span>
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card__header">
          <h2 className="card__title">Version compare</h2>
          <div className="row">
            <label className="topbar__env">
              <span className="field__label">A</span>
              <select value={left} onChange={(e) => setLeft(Number(e.target.value))}>
                {versions.map((v) => (
                  <option key={v} value={v}>
                    v{v}
                  </option>
                ))}
              </select>
            </label>
            <label className="topbar__env">
              <span className="field__label">B</span>
              <select value={right} onChange={(e) => setRight(Number(e.target.value))}>
                {versions.map((v) => (
                  <option key={v} value={v}>
                    v{v}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        <div className="card__body">
          {left !== spec.version && right !== spec.version ? (
            <PlaceholderBanner note="Both selected versions are historical; only the current version body is cached in the console." />
          ) : null}
          <div className="compare">
            <CompareColumn spec={spec} version={left} />
            <CompareColumn spec={spec} version={right} />
          </div>
        </div>
      </section>
    </div>
  );
}
