/** Primary navigation sidebar for the LLMOps Console. */
import { NavLink } from 'react-router-dom';

interface NavItem {
  to: string;
  label: string;
  icon: string;
  end?: boolean;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    label: 'Overview',
    items: [{ to: '/', label: 'Dashboard', icon: '◧', end: true }],
  },
  {
    label: 'Build',
    items: [
      { to: '/prompts', label: 'Prompts', icon: '✎' },
      { to: '/models', label: 'Models', icon: '⬡' },
      { to: '/agents', label: 'Agents', icon: '⌥' },
    ],
  },
  {
    label: 'Assure',
    items: [
      { to: '/evaluations', label: 'Evaluations', icon: '✓' },
      { to: '/guardrails', label: 'Guardrails', icon: '⛨' },
    ],
  },
  {
    label: 'Operate',
    items: [
      { to: '/traces', label: 'Traces', icon: '⦿' },
      { to: '/costs', label: 'Costs', icon: '$' },
      { to: '/feedback', label: 'Feedback', icon: '☺' },
    ],
  },
  {
    label: 'Adopt',
    items: [{ to: '/onboarding', label: 'Onboarding', icon: '☑' }],
  },
];

export function Sidebar(): JSX.Element {
  return (
    <nav className="sidebar" aria-label="Primary">
      <div className="sidebar__brand">
        <span className="sidebar__mark" aria-hidden="true">
          L
        </span>
        <span>LLMOps Console</span>
      </div>
      <div className="sidebar__nav">
        {SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="sidebar__section-label">{section.label}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `sidebar__link${isActive ? ' is-active' : ''}`
                }
              >
                <span className="sidebar__icon" aria-hidden="true">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </div>
      <div className="sidebar__footer">Reusable LLMOps platform · console</div>
    </nav>
  );
}
