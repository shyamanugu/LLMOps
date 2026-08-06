/** Prompts list page. */
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { AsyncSection } from '../components/AsyncSection';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/MetricBadge';
import { usePrompts } from '../hooks/usePrompts';
import type { PromptSummary } from '../api/types';

export function Prompts(): JSX.Element {
  const query = usePrompts();
  const navigate = useNavigate();

  const columns: ReadonlyArray<Column<PromptSummary>> = [
    { id: 'id', header: 'Prompt', render: (p) => <span className="mono">{p.id}</span> },
    { id: 'version', header: 'Version', numeric: true, render: (p) => `v${p.version}` },
    { id: 'alias', header: 'Model alias', render: (p) => <Badge tone="info">{p.model_alias}</Badge> },
    {
      id: 'labels',
      header: 'Labels',
      render: (p) => (
        <span className="chip-row">
          {p.labels.map((l) => (
            <Badge key={l}>{l}</Badge>
          ))}
        </span>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Prompts"
        subtitle="Versioned prompt registry. Select a prompt to inspect and compare versions."
      />
      <section className="card">
        <div className="card__body">
          <AsyncSection query={query}>
            {(rows) => (
              <DataTable
                columns={columns}
                rows={rows}
                rowKey={(p) => p.id}
                onRowClick={(p) => navigate(`/prompts/${encodeURIComponent(p.id)}`)}
                emptyTitle="No prompts registered"
                emptyDescription="Add .prompt.yaml files under usecases/*/prompts to see them here."
                caption="Registered prompts"
              />
            )}
          </AsyncSection>
        </div>
      </section>
    </>
  );
}
