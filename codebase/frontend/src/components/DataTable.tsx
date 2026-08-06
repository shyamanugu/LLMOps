/**
 * Generic, fully-typed data table.
 *
 * Columns declare how to render a cell for a row of type `T`. Rows are keyed by
 * a caller-supplied accessor. Optional row-click support and an empty state.
 */
import type { ReactNode } from 'react';
import { EmptyState } from './EmptyState';

export interface Column<T> {
  /** Stable column id. */
  id: string;
  /** Header label. */
  header: string;
  /** Cell renderer for a row. */
  render: (row: T) => ReactNode;
  /** Right-align numeric columns. */
  numeric?: boolean;
  /** Optional fixed width (CSS value). */
  width?: string;
}

interface DataTableProps<T> {
  columns: ReadonlyArray<Column<T>>;
  rows: ReadonlyArray<T>;
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
  caption?: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyTitle,
  emptyDescription,
  caption,
}: DataTableProps<T>): JSX.Element {
  if (rows.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.id}
                scope="col"
                className={col.numeric ? 'data-table__num' : undefined}
                style={col.width ? { width: col.width } : undefined}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const clickable = Boolean(onRowClick);
            return (
              <tr
                key={rowKey(row)}
                className={clickable ? 'is-clickable' : undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                tabIndex={clickable ? 0 : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          onRowClick(row);
                        }
                      }
                    : undefined
                }
              >
                {columns.map((col) => (
                  <td key={col.id} className={col.numeric ? 'data-table__num' : undefined}>
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
