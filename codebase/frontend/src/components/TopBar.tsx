/** Top bar: page title, environment switch and live health indicator. */
import { useHealth } from '../hooks/useHealth';
import { useUI } from '../store/UIContext';
import type { Environment } from '../api/types';

const ENVIRONMENTS: Environment[] = ['dev', 'test', 'prod'];

interface TopBarProps {
  title: string;
}

export function TopBar({ title }: TopBarProps): JSX.Element {
  const { environment, setEnvironment } = useUI();
  const { data } = useHealth();

  const status = data?.data.status ?? 'down';
  const isUp = status === 'ok';
  const dotClass = isUp ? 'is-up' : status === 'down' ? 'is-down' : '';

  return (
    <header className="topbar">
      <div className="topbar__title">{title}</div>
      <div className="topbar__right">
        <label className="topbar__env">
          <span className="sr-only">Environment</span>
          <span>env</span>
          <select
            value={environment}
            onChange={(event) => setEnvironment(event.target.value as Environment)}
            aria-label="Select environment"
          >
            {ENVIRONMENTS.map((env) => (
              <option key={env} value={env}>
                {env}
              </option>
            ))}
          </select>
        </label>
        <span className="topbar__env" title={`API status: ${status}`}>
          <span className={`topbar__health-dot ${dotClass}`} aria-hidden="true" />
          <span>{isUp ? 'healthy' : status}</span>
        </span>
      </div>
    </header>
  );
}
