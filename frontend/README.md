# Frontend

React/Vite interface for Tonight's Pick.

## Commands

From this directory:

```bash
npm ci
npm run dev
npm run lint
npm test -- --run
npm run build
```

The application reads the backend URL from `VITE_API_BASE_URL` and defaults to
`http://localhost:8081`. Create `.env.local` to override it:

```bash
VITE_API_BASE_URL=http://localhost:8081
```

## Structure

```text
src/
  components/   reusable layout, media, routing, and UI components
  config/       runtime environment configuration
  hooks/        authentication and application state orchestration
  mappers/      API-to-view-model transformations
  pages/        routed application pages
  services/     HTTP client and resource APIs
  styles/       design tokens
```

The frontend covers authentication, preference onboarding, catalogue discovery, ratings, personalized recommendations,
and profile management. Shared visual tokens live in `src/styles/tokens.css`; concrete page and component rules live
in `src/index.css`.
