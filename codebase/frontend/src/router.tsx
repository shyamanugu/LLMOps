/** Route table for the LLMOps Console (React Router v6), covering all §4 pages. */
import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Prompts } from './pages/Prompts';
import { PromptDetail } from './pages/PromptDetail';
import { Models } from './pages/Models';
import { Evaluations } from './pages/Evaluations';
import { Traces } from './pages/Traces';
import { TraceDetail } from './pages/TraceDetail';
import { Costs } from './pages/Costs';
import { Agents } from './pages/Agents';
import { Guardrails } from './pages/Guardrails';
import { Feedback } from './pages/Feedback';
import { Onboarding } from './pages/Onboarding';
import { NotFound } from './pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'prompts', element: <Prompts /> },
      { path: 'prompts/:id', element: <PromptDetail /> },
      { path: 'models', element: <Models /> },
      { path: 'evaluations', element: <Evaluations /> },
      { path: 'traces', element: <Traces /> },
      { path: 'traces/:id', element: <TraceDetail /> },
      { path: 'costs', element: <Costs /> },
      { path: 'agents', element: <Agents /> },
      { path: 'guardrails', element: <Guardrails /> },
      { path: 'feedback', element: <Feedback /> },
      { path: 'onboarding', element: <Onboarding /> },
      { path: '*', element: <NotFound /> },
    ],
  },
]);
