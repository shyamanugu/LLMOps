/**
 * Renders the loading / error / placeholder / success states for a React Query
 * result whose payload is a {@link Resulted}. Keeps pages free of repetitive
 * status branching and guarantees the console never crashes on TODO endpoints.
 */
import type { ReactNode } from 'react';
import type { UseQueryResult } from '@tanstack/react-query';
import type { Resulted } from '../api/client';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';
import { PlaceholderBanner } from './PlaceholderBanner';

interface AsyncSectionProps<T> {
  query: UseQueryResult<Resulted<T>>;
  children: (data: T) => ReactNode;
  loadingLabel?: string;
}

export function AsyncSection<T>({
  query,
  children,
  loadingLabel,
}: AsyncSectionProps<T>): JSX.Element {
  if (query.isPending) {
    return <LoadingState label={loadingLabel} />;
  }
  if (query.isError) {
    return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  }
  const { data, isPlaceholder, note } = query.data;
  return (
    <>
      {isPlaceholder ? <PlaceholderBanner note={note} /> : null}
      {children(data)}
    </>
  );
}
