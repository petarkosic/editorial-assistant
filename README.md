# Editorial Assistant

A multi-agent editorial pipeline with a human-in-the-loop web UI: scout breaking
news, research it, and draft articles from it — approving or rejecting at each
stage, with an LLM-as-judge quality score alongside every approval.

## Status

| Stage                                                                | Status      |
| -------------------------------------------------------------------- | ----------- |
| Scout — monitor an RSS feed, score importance, judge quality         | **Working** |
| Research — agentic tool-calling loop (search + fetch), judge quality | Not built   |
| Synthesis — draft an article from a brief, judge quality             | Not built   |
| Offline evaluation suite                                             | Not built   |

## Architecture

```text
scout_agent/  →  research_agent/  →  synthesis_agent/     (framework-free, one LLM call each)
      \               |                    /
       \              |                   /
        \-------- evaluation/  ----------/                  (LLM-as-judge, per stage)
                       |
                  backend/ (FastAPI, Postgres via SQLAlchemy + Alembic)
                       |
                  frontend/ (React + Vite)
```

## Running it locally

```bash
docker compose up -d db
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --port 8000
```

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `.env` and set a real `OPENAI_API_KEY` (Gemini, via
[AI Studio](https://aistudio.google.com/)) for the scout to actually run.

## Project layout

- `common/` — shared config, LLM client, pydantic domain models.
- `scout_agent/`, `research_agent/`, `synthesis_agent/` — the three pipeline
  agents, one LLM call each.
- `evaluation/` — the LLM-as-judge (`Judge`), one rubric per stage.
- `backend/` — FastAPI app, Postgres models, background task pipeline,
  `/api/*` routes.
- `frontend/` — React + Vite web UI.
