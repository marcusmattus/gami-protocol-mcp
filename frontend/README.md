# Frontend Overlay

This directory contains Horizon UI-ready components, hooks, and configuration that mirror the production dashboard living in `../gami-protocol-universal-engagement-layer`.

- `src/hooks/useAgentStream.ts` streams SSE data from the FastAPI backend.
- `components/*` implements Layout, Cards, Kanban, and ComplexTable widgets compatible with the Horizon UI system.
- `views/Dashboard.tsx` composes the widgets into the primary supervisor view.

> **Tip:** Copy the files from `src/` into the full dashboard repo to keep design tokens and assets centralized. The Docker Compose service ships the actual React app from `../gami-protocol-universal-engagement-layer`, so this overlay mainly document the contract (API + SX patterns).
