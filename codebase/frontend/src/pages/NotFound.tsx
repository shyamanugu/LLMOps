/** 404 fallback page. */
import { Link } from 'react-router-dom';
import { EmptyState } from '../components/EmptyState';

export function NotFound(): JSX.Element {
  return (
    <EmptyState
      icon="404"
      title="Page not found"
      description="The page you requested does not exist in the console."
      action={
        <Link to="/" className="btn btn--primary btn--sm">
          Back to dashboard
        </Link>
      }
    />
  );
}
