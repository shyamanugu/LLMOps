/** Models page: alias -> deployment table for the selected environment. */
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/MetricBadge';
import { useModels } from '../hooks/useModels';
import { useUI } from '../store/UIContext';
import type { ModelAlias } from '../api/types';

export function Models(): JSX.Element {
  const { environment } = useUI();
  const query = useModels(environment);

  const columns: ReadonlyArray<Column<ModelAlias>> = [
    { id: 'alias', header: 'Alias', render: (m) => <strong>{m.alias}</strong> },
    { id: 'deployment', header: 'Deployment', render: (m) => <span className="mono">{m.deployment}</span> },
    { id: 'kind', header: 'Kind', render: (m) => <Badge tone="neutral">{m.kind}</Badge> },
    { id: 'env', header: 'Environment', render: (m) => <Badge tone="info">{m.environment}</Badge> },
    { id: 'desc', header: 'Description', render: (m) => <span className="muted">{m.description}</span> },
  ];

  return (
    <>
      <PageHeader
        title="Models"
        subtitle={`Alias resolution for the "${environment}" environment (from platform/models.yaml).`}
      />
      <section className="card">
        <div className="card__body">
          <AsyncSection query={query} loadingLabel="Resolving model aliases…">
            {(rows) => (
              <DataTable
                columns={columns}
                rows={rows}
                rowKey={(m) => m.alias}
                caption="Model aliases"
                emptyTitle="No aliases configured"
              />
            )}
          </AsyncSection>
        </div>
      </section>
    </>
  );
}
