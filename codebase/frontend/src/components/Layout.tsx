/** App shell: sidebar + top bar + routed content area. */
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

/** Maps a path prefix to the human title shown in the top bar. */
const TITLES: ReadonlyArray<[string, string]> = [
  ['/prompts', 'Prompts'],
  ['/models', 'Models'],
  ['/evaluations', 'Evaluations'],
  ['/traces', 'Traces'],
  ['/costs', 'Costs'],
  ['/agents', 'Agents'],
  ['/guardrails', 'Guardrails'],
  ['/feedback', 'Feedback'],
  ['/onboarding', 'Onboarding'],
];

function titleFor(pathname: string): string {
  if (pathname === '/') return 'Dashboard';
  const match = TITLES.find(([prefix]) => pathname.startsWith(prefix));
  return match ? match[1] : 'LLMOps Console';
}

export function Layout(): JSX.Element {
  const location = useLocation();
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar title={titleFor(location.pathname)} />
        <main className="app-content" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
