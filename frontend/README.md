# Editorial Assistant — Frontend

Vite + React 18 + TypeScript. Separate npm project from the root Python backend.
No auth yet — deferred for the MVP (see the root spec, Section 7).

## Requirements

- Node 20+

## Commands

| Command | Purpose |
|---|---|
| `npm install` | install dependencies |
| `npm run dev` | dev server on http://localhost:5173, proxies `/api` → `http://localhost:8000` |
| `npm run typecheck` | `tsc -b --noEmit` |
| `npm run build` | type-check then `vite build` → `dist/` |

## Backend dependency

The dev server proxies `/api` to the FastAPI backend on port 8000. Start it from the
repo root (`uv run uvicorn backend.main:app --port 8000`) before `npm run dev`.

## Architecture

- Runs list + New Run dialog + run detail (scout report, story list, scout
  evaluation scorecard) — the scout slice. Story rows are placeholders until
  the research slice wires the per-story stage view.
