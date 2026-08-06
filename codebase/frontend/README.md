# LLMOps Console

The operator console for the LLMOps platform — a Vite + React 18 + TypeScript single-page
app that views every platform surface: prompts, models, evaluations, traces, costs, guardrails,
agents, feedback and use-case onboarding.

It is a **read-mostly** console over the FastAPI backend (`/api/v1`). Where a backend endpoint is
still a placeholder (for example trace read-through, or the evaluation runner), the console renders
a clearly-labelled **"Placeholder data"** banner and coherent sample data instead of crashing.

## Stack

- **Vite 5** + **React 18** + **TypeScript** (strict, no `any`)
- **React Router v6** for routing
- **TanStack React Query v5** for data fetching / caching
- **ESLint** (typescript-eslint, react-hooks) — the repo standard is ESLint-clean
- Plain CSS design tokens (navy `#1F3A5F` + teal `#2A9D8F` + neutral grays), light and accessible

## Getting started

```bash
cd frontend
cp .env.example .env        # set VITE_API_BASE to your backend
npm install
npm run dev                 # http://localhost:5173
```

### Environment

The API base URL is read from `import.meta.env.VITE_API_BASE`:

```
VITE_API_BASE=http://localhost:8000/api/v1
```

## Scripts

| Script              | Purpose                                        |
| ------------------- | ---------------------------------------------- |
| `npm run dev`       | Start the Vite dev server                      |
| `npm run build`     | Type-check (`tsc -b`) and produce `dist/`      |
| `npm run preview`   | Serve the production build locally             |
| `npm run lint`      | ESLint (fails on any warning)                  |
| `npm run typecheck` | `tsc --noEmit`                                 |

## Project structure

```
src/
├─ main.tsx              # entrypoint
├─ App.tsx               # React Query + UI providers + router
├─ router.tsx            # all §4 routes
├─ api/
│  ├─ client.ts          # typed fetch wrapper, ApiError, placeholder fallback
│  ├─ types.ts           # TS types mirroring backend pydantic models
│  └─ endpoints/*        # one module per resource
├─ components/           # Layout, Sidebar, TopBar, DataTable, StatTile, SpanTree, …
├─ pages/                # Dashboard, Prompts(+Detail), Models, Evaluations, Traces(+Detail), …
├─ hooks/                # React Query hooks, one per resource
├─ store/                # light global UI state (React Context)
├─ lib/                  # formatting helpers
└─ theme/                # design tokens + global.css
```

## Routes

`/` Dashboard · `/prompts` (+ `/prompts/:id` version compare) · `/models` · `/evaluations`
· `/traces` (+ `/traces/:id` span tree) · `/costs` · `/agents` · `/guardrails` · `/feedback`
· `/onboarding`.

## Placeholder / "not wired yet" handling

Every endpoint call goes through `withPlaceholder(...)` in `api/client.ts`. If the request fails
because the endpoint is unreachable / missing / not implemented (network error, HTTP 404 or 501),
the console falls back to typed sample data and flags it via `Resulted<T>.isPlaceholder`. The
`AsyncSection` component then renders a `PlaceholderBanner`. Real errors (500, 4xx other than 404)
render an `ErrorState` with a retry action. The app never crashes on a missing endpoint.

## Docker

Multi-stage build to a static nginx image:

```bash
docker build -t llmops-console --build-arg VITE_API_BASE=https://api.example.com/api/v1 .
docker run -p 8080:80 llmops-console   # http://localhost:8080
```

`nginx.conf` serves the SPA with history-mode routing, long-cache immutable assets, a
non-cached HTML shell, and baseline security headers.

## Accessibility

- Semantic landmarks (`nav`, `header`, `main`), a skip-friendly `#main-content` region.
- Keyboard-operable tables (row `Enter`/`Space`), tree (`role="tree"`), and visible focus rings.
- Live regions on loading (`role="status"`) and error (`role="alert"`) states.
- Color choices meet contrast against the light background.
