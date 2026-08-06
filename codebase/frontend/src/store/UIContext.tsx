/**
 * Light global UI state via React Context (no external store library).
 *
 * Holds the currently-selected environment (dev|test|prod) which several pages
 * use to scope their queries, plus a compact-sidebar toggle. Kept intentionally
 * small — data state lives in React Query, not here.
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { Environment } from '../api/types';

interface UIState {
  environment: Environment;
  setEnvironment: (env: Environment) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

const UIContext = createContext<UIState | undefined>(undefined);

const STORAGE_KEY = 'llmops.ui.environment';

function readInitialEnv(): Environment {
  const stored =
    typeof window !== 'undefined' ? window.localStorage.getItem(STORAGE_KEY) : null;
  if (stored === 'dev' || stored === 'test' || stored === 'prod') {
    return stored;
  }
  return 'dev';
}

export function UIProvider({ children }: { children: ReactNode }): JSX.Element {
  const [environment, setEnvState] = useState<Environment>(readInitialEnv);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const setEnvironment = useCallback((env: Environment) => {
    setEnvState(env);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, env);
    }
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const value = useMemo<UIState>(
    () => ({ environment, setEnvironment, sidebarCollapsed, toggleSidebar }),
    [environment, setEnvironment, sidebarCollapsed, toggleSidebar],
  );

  return <UIContext.Provider value={value}>{children}</UIContext.Provider>;
}

/** Access the global UI state; throws if used outside the provider. */
// eslint-disable-next-line react-refresh/only-export-components -- hook colocated with its provider
export function useUI(): UIState {
  const ctx = useContext(UIContext);
  if (!ctx) {
    throw new Error('useUI must be used within a UIProvider');
  }
  return ctx;
}
